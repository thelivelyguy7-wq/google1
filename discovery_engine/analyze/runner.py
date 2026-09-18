from __future__ import annotations

import hashlib
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed

import anthropic

from ..config import settings
from ..store import Store, now_iso
from ..validate import validate_analysis
from .heuristic import HeuristicAnalyzer
from .llm import AnalysisSkipped, ClaudeAnalyzer, claude_available


NO_CREDENTIALS = ("No Claude credentials found. Set ANTHROPIC_API_KEY (or ANTHROPIC_AUTH_TOKEN, or run `ant auth login`), "
                  "or use --analyzer heuristic to run offline.")


def get_analyzer(kind: str = "auto"):
    if kind == "claude":
        if not claude_available():
            raise SystemExit(NO_CREDENTIALS)
        return ClaudeAnalyzer()
    if kind == "auto" and claude_available():
        return ClaudeAnalyzer()
    return HeuristicAnalyzer()


def pending_chunks(store: Store, analyzer_name: str, reanalyze: bool, limit: int | None, dataset: str | None) -> list[dict]:
    sql = """SELECT c.chunk_id, c.record_id, c.text, r.title, r.platform, r.thread_context, r.created_at
             FROM chunks c JOIN records r ON r.record_id = c.record_id
             WHERE r.duplicate_of IS NULL"""
    params: list = []
    if dataset:
        sql += " AND r.dataset = ?"
        params.append(dataset)
    if not reanalyze:
        sql += " AND NOT EXISTS (SELECT 1 FROM analyses a WHERE a.chunk_id = c.chunk_id AND a.is_current = 1 AND a.analyzer = ?)"
        params.append(analyzer_name)
    sql += " ORDER BY c.chunk_id"
    if limit:
        sql += f" LIMIT {int(limit)}"
    return store.q(sql, tuple(params))


def _persist(store: Store, analyzer, chunk: dict, payload: dict, model: str | None) -> dict:
    # uuid4 component: a timestamp alone collides when a chunk is re-analysed within the same second.
    analysis_id = "AN-" + hashlib.sha1(f"{chunk['chunk_id']}|{analyzer.name}|{uuid.uuid4()}".encode()).hexdigest()[:12]
    # Quotes are validated against exactly the text the analyzer saw.
    source_text = f"{chunk['title']}\n{chunk['text']}" if chunk.get("title") else chunk["text"]
    payload, signals, report = validate_analysis(payload, source_text, analysis_id, chunk["record_id"])
    store.save_analysis({
        "analysis_id": analysis_id, "chunk_id": chunk["chunk_id"], "record_id": chunk["record_id"],
        "analyzer": analyzer.name, "model": model, "prompt_version": analyzer.prompt_version,
        "created_at": now_iso(), "relevant": int(bool(payload.get("relevant"))),
        "confidence": float(payload.get("confidence") or 0), "payload": payload, **report,
    }, signals)
    return report


def run_analysis(store: Store, analyzer_kind: str = "auto", reanalyze: bool = False, limit: int | None = None,
                 dataset: str | None = None, progress=print) -> dict:
    analyzer = get_analyzer(analyzer_kind)
    chunks = pending_chunks(store, analyzer.name, reanalyze, limit, dataset)
    stats = {"analyzer": analyzer.name, "chunks": len(chunks), "analyzed": 0, "skipped": 0,
             "quotes_total": 0, "quotes_invalid": 0, "errors": []}
    progress(f"Analyzing {len(chunks)} chunks with {analyzer.name}")

    def work(chunk):
        return chunk, *analyzer.analyze(chunk["text"], chunk)

    workers = settings.concurrency if analyzer.name == "claude" else 1
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(work, c) for c in chunks]
        for i, fut in enumerate(as_completed(futures), 1):
            try:
                chunk, payload, model = fut.result()
            except AnalysisSkipped as e:
                stats["skipped"] += 1
                stats["errors"].append(str(e))
                continue
            except anthropic.AuthenticationError:
                pool.shutdown(cancel_futures=True)
                raise SystemExit("Claude credentials rejected. Set ANTHROPIC_API_KEY or run with --analyzer heuristic.")
            except TypeError as e:  # the SDK raises TypeError when no authentication method resolves at request time
                if "authentication method" not in str(e):
                    raise
                pool.shutdown(cancel_futures=True)
                raise SystemExit(NO_CREDENTIALS)
            except anthropic.APIError as e:  # rate limits / 5xx after SDK retries: record and continue
                stats["skipped"] += 1
                stats["errors"].append(f"{type(e).__name__}: {e}")
                continue
            report = _persist(store, analyzer, chunk, payload, model)
            stats["analyzed"] += 1
            stats["quotes_total"] += report["quotes_total"]
            stats["quotes_invalid"] += report["quotes_invalid"]
            if i % 100 == 0:
                progress(f"  {i}/{len(chunks)}")
    stats["errors"] = stats["errors"][:20]
    return stats
