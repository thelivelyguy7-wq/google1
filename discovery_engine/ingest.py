"""COLLECT -> CLEAN -> DEDUPLICATE -> CHUNK (spec §9, §11)."""
from __future__ import annotations

import hashlib
import html
import json
import re
from pathlib import Path

import pandas as pd

from .config import settings
from .models import RawRecord
from .store import Store, now_iso

# Accept common column names from exported datasets.
FIELD_ALIASES = {
    "text": ["text", "body", "content", "review", "comment", "selftext", "message", "review_text"],
    "title": ["title", "subject", "headline"],
    "source": ["source"],
    "platform": ["platform", "subreddit", "store", "site"],
    "source_url": ["source_url", "url", "permalink", "link"],
    "source_id": ["source_id", "id", "review_id", "comment_id", "post_id"],
    "created_at": ["created_at", "date", "timestamp", "at", "created_utc", "published_at"],
    "thread_context": ["thread_context", "thread", "video_title", "thread_title"],
    "parent_text": ["parent_text", "parent", "parent_comment"],
    "author": ["author", "user", "username", "userName"],
}

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d\s-]{8,}\d)(?!\w)")


def clean_text(text: str) -> str:
    text = html.unescape(str(text or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    text = EMAIL_RE.sub("[email removed]", text)
    text = PHONE_RE.sub("[number removed]", text)
    return re.sub(r"[ \t]+", " ", text).strip()


def normalize_for_hash(text: str) -> str:
    return re.sub(r"\W+", " ", text.lower()).strip()


def content_hash(text: str) -> str:
    return hashlib.sha256(normalize_for_hash(text).encode()).hexdigest()[:24]


def author_hash(author: str | None) -> str | None:
    if not author:
        return None
    return hashlib.sha256((settings.author_salt + str(author)).encode()).hexdigest()[:12]


def shingles(text: str, k: int = 5) -> set[str]:
    words = normalize_for_hash(text).split()
    return {" ".join(words[i:i + k]) for i in range(max(1, len(words) - k + 1))}


def jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if a and b else 0.0


def chunk_text(text: str, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks, cur = [], ""
    for s in sentences:
        if cur and len(cur) + len(s) + 1 > max_chars:
            chunks.append(cur)
            cur = s
        else:
            cur = f"{cur} {s}".strip()
    if cur:
        chunks.append(cur)
    return chunks


# ---------------------------------------------------------------------------
def load_rows(path: str | Path) -> list[dict]:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path).fillna("").to_dict("records")
    if suffix in (".xlsx", ".xls"):
        return pd.read_excel(path).fillna("").to_dict("records")
    if suffix == ".jsonl":
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else data.get("records", [data])
    if suffix == ".txt":
        # One record per blank-line separated block.
        blocks = [b.strip() for b in re.split(r"\n\s*\n", path.read_text(encoding="utf-8")) if b.strip()]
        return [{"text": b, "source_id": f"{path.stem}-{i}"} for i, b in enumerate(blocks)]
    raise ValueError(f"Unsupported file type: {suffix}")


def _pick(row: dict, field: str):
    for alias in FIELD_ALIASES.get(field, [field]):
        if alias in row and row[alias] not in (None, ""):
            return row[alias]
    return None


def to_record(row: dict, default_source: str, dataset: str, is_synthetic: bool | None) -> RawRecord | None:
    text = clean_text(_pick(row, "text") or "")
    if len(text) < 15:
        return None
    source = str(_pick(row, "source") or default_source)
    source_id = str(_pick(row, "source_id") or content_hash(text))
    replies = row.get("replies") or []
    if isinstance(replies, str):
        try:
            replies = json.loads(replies)
        except json.JSONDecodeError:
            replies = [replies]
    engagement = row.get("engagement") or {}
    if isinstance(engagement, str):
        try:
            engagement = json.loads(engagement)
        except json.JSONDecodeError:
            engagement = {}
    synthetic = bool(row.get("is_synthetic")) if is_synthetic is None else is_synthetic
    return RawRecord(
        record_id=f"{source}:{source_id}",
        source=source,
        platform=str(_pick(row, "platform") or source),
        source_url=_pick(row, "source_url"),
        source_id=source_id,
        title=clean_text(_pick(row, "title") or "") or None,
        text=text,
        thread_context=clean_text(_pick(row, "thread_context") or "") or None,
        parent_text=clean_text(_pick(row, "parent_text") or "") or None,
        replies=[clean_text(r) for r in replies],
        engagement=engagement,
        created_at=str(_pick(row, "created_at")) if _pick(row, "created_at") else None,
        retrieved_at=row.get("retrieved_at") or now_iso(),
        author_hash=author_hash(_pick(row, "author")),
        is_synthetic=synthetic,
        dataset=dataset,
    )


def ingest_file(store: Store, path: str | Path, source: str | None = None, dataset: str = "default",
                is_synthetic: bool | None = None, near_dup_threshold: float = 0.9) -> dict:
    path = Path(path)
    rows = load_rows(path)
    stats = {"rows": len(rows), "inserted": 0, "skipped_short": 0, "already_present": 0,
             "exact_duplicates": 0, "near_duplicates": 0}

    existing = store.q("SELECT record_id, content_hash, text FROM records WHERE duplicate_of IS NULL")
    by_hash = {r["content_hash"]: r["record_id"] for r in existing}
    known_ids = {r["record_id"] for r in store.q("SELECT record_id FROM records")}
    shingle_index = [(r["record_id"], shingles(r["text"])) for r in existing]

    with store.tx():
        for row in rows:
            rec = to_record(row, source or path.stem, dataset, is_synthetic)
            if rec is None:
                stats["skipped_short"] += 1
                continue
            if rec.record_id in known_ids:
                stats["already_present"] += 1
                continue
            full_text = f"{rec.title}. {rec.text}" if rec.title else rec.text
            h = content_hash(full_text)
            dup_of = by_hash.get(h)
            if dup_of:
                stats["exact_duplicates"] += 1
            else:
                sh = shingles(full_text)
                # Near-dup check is O(n); fine for tens of thousands of short records.
                for rid, other in shingle_index:
                    if len(sh) > 8 and jaccard(sh, other) >= near_dup_threshold:
                        dup_of = rid
                        stats["near_duplicates"] += 1
                        break
                if not dup_of:
                    by_hash[h] = rec.record_id
                    shingle_index.append((rec.record_id, sh))
            store.insert_record({**rec.model_dump(), "content_hash": h, "duplicate_of": dup_of})
            known_ids.add(rec.record_id)
            stats["inserted"] += 1
            if not dup_of:
                for i, chunk in enumerate(chunk_text(rec.text, settings.chunk_chars)):
                    store.insert_chunk(f"{rec.record_id}#{i}", rec.record_id, i, chunk)
    return stats
