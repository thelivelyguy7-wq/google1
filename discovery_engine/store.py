"""SQLite persistence.

Tables are split so RAW EVIDENCE (records, chunks) is never mutated by the AI
layer (analyses, signals, syntheses). PM corrections live in `overrides` and are
applied on read, so the original AI output stays auditable.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS records (
    record_id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    platform TEXT NOT NULL,
    source_url TEXT,
    source_id TEXT,
    title TEXT,
    text TEXT NOT NULL,
    thread_context TEXT,
    parent_text TEXT,
    replies TEXT,
    engagement TEXT,
    created_at TEXT,
    retrieved_at TEXT,
    author_hash TEXT,
    is_synthetic INTEGER NOT NULL DEFAULT 0,
    dataset TEXT NOT NULL DEFAULT 'default',
    content_hash TEXT NOT NULL,
    duplicate_of TEXT,
    ingested_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_records_hash ON records(content_hash);

CREATE TABLE IF NOT EXISTS chunks (
    chunk_id TEXT PRIMARY KEY,
    record_id TEXT NOT NULL REFERENCES records(record_id),
    idx INTEGER NOT NULL,
    text TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS analyses (
    analysis_id TEXT PRIMARY KEY,
    chunk_id TEXT NOT NULL REFERENCES chunks(chunk_id),
    record_id TEXT NOT NULL,
    analyzer TEXT NOT NULL,
    model TEXT,
    prompt_version TEXT NOT NULL,
    created_at TEXT NOT NULL,
    relevant INTEGER NOT NULL,
    confidence REAL,
    quotes_total INTEGER,
    quotes_invalid INTEGER,
    payload TEXT NOT NULL,
    is_current INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX IF NOT EXISTS idx_analyses_chunk ON analyses(chunk_id, is_current);

CREATE TABLE IF NOT EXISTS signals (
    evidence_id TEXT PRIMARY KEY,
    analysis_id TEXT NOT NULL REFERENCES analyses(analysis_id),
    record_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    label TEXT NOT NULL,
    value TEXT,
    quote TEXT,
    quote_valid INTEGER NOT NULL,
    precision TEXT
);
CREATE INDEX IF NOT EXISTS idx_signals_kind ON signals(kind, label);

CREATE TABLE IF NOT EXISTS overrides (
    override_id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    field TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    note TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS syntheses (
    synthesis_id INTEGER PRIMARY KEY AUTOINCREMENT,
    kind TEXT NOT NULL,
    created_at TEXT NOT NULL,
    params TEXT,
    payload TEXT NOT NULL
);
"""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Store:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA)

    @contextmanager
    def tx(self):
        try:
            yield self.conn
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    def q(self, sql: str, params: tuple | dict = ()) -> list[dict]:
        return [dict(r) for r in self.conn.execute(sql, params).fetchall()]

    # -- raw evidence ------------------------------------------------------
    def insert_record(self, rec: dict) -> None:
        cols = ["record_id", "source", "platform", "source_url", "source_id", "title", "text",
                "thread_context", "parent_text", "replies", "engagement", "created_at",
                "retrieved_at", "author_hash", "is_synthetic", "dataset", "content_hash",
                "duplicate_of", "ingested_at"]
        row = dict(rec)
        row["replies"] = json.dumps(row.get("replies") or [])
        row["engagement"] = json.dumps(row.get("engagement") or {})
        row["is_synthetic"] = int(bool(row.get("is_synthetic")))
        row["ingested_at"] = now_iso()
        self.conn.execute(
            f"INSERT OR IGNORE INTO records ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
            [row.get(c) for c in cols],
        )

    def insert_chunk(self, chunk_id: str, record_id: str, idx: int, text: str) -> None:
        self.conn.execute("INSERT OR IGNORE INTO chunks VALUES (?,?,?,?)", (chunk_id, record_id, idx, text))

    # -- AI interpretation -------------------------------------------------
    def save_analysis(self, analysis: dict, signals: list[dict]) -> None:
        with self.tx() as c:
            c.execute("UPDATE analyses SET is_current = 0 WHERE chunk_id = ?", (analysis["chunk_id"],))
            c.execute(
                "INSERT INTO analyses VALUES (:analysis_id,:chunk_id,:record_id,:analyzer,:model,"
                ":prompt_version,:created_at,:relevant,:confidence,:quotes_total,:quotes_invalid,:payload,1)",
                {**analysis, "payload": json.dumps(analysis["payload"], ensure_ascii=False)},
            )
            c.executemany(
                "INSERT INTO signals VALUES (:evidence_id,:analysis_id,:record_id,:kind,:label,:value,"
                ":quote,:quote_valid,:precision)",
                signals,
            )

    def selected_target_segment(self) -> str | None:
        """The segment the PM picked for primary research, if any (latest choice wins)."""
        rows = self.q("SELECT new_value FROM overrides WHERE target_type = 'study' AND field = 'target_segment'"
                      " ORDER BY override_id DESC LIMIT 1")
        return json.loads(rows[0]["new_value"]) if rows else None

    def selected_target_opportunity(self) -> str | None:
        """The opportunity the PM picked for discovery focus, if any (latest choice wins)."""
        rows = self.q("SELECT new_value FROM overrides WHERE target_type = 'study' AND field = 'target_opportunity'"
                      " ORDER BY override_id DESC LIMIT 1")
        return json.loads(rows[0]["new_value"]) if rows else None

    def add_override(self, target_type: str, target_id: str, field: str, old, new, note: str = "") -> None:
        with self.tx() as c:
            c.execute(
                "INSERT INTO overrides (target_type,target_id,field,old_value,new_value,note,created_at)"
                " VALUES (?,?,?,?,?,?,?)",
                (target_type, target_id, field, json.dumps(old), json.dumps(new), note, now_iso()),
            )

    def save_synthesis(self, kind: str, payload: dict, params: dict | None = None) -> int:
        with self.tx() as c:
            cur = c.execute(
                "INSERT INTO syntheses (kind, created_at, params, payload) VALUES (?,?,?,?)",
                (kind, now_iso(), json.dumps(params or {}), json.dumps(payload, ensure_ascii=False)),
            )
            return cur.lastrowid

    def latest_synthesis(self, kind: str) -> dict | None:
        rows = self.q("SELECT * FROM syntheses WHERE kind = ? ORDER BY synthesis_id DESC LIMIT 1", (kind,))
        if not rows:
            return None
        row = rows[0]
        row["payload"] = json.loads(row["payload"])
        row["params"] = json.loads(row["params"] or "{}")
        return row

    # -- views ---------------------------------------------------------------
    def current_analyses(self, include_synthetic: bool = True) -> list[dict]:
        """Current analyses joined to raw record metadata, with PM overrides applied."""
        rows = self.q(
            """SELECT a.*, r.source, r.platform, r.source_url, r.created_at AS source_date,
                      r.is_synthetic, r.title, r.dataset, r.thread_context
               FROM analyses a JOIN records r ON r.record_id = a.record_id
               WHERE a.is_current = 1 AND r.duplicate_of IS NULL"""
            + ("" if include_synthetic else " AND r.is_synthetic = 0")
        )
        overrides = self._overrides_by_target("analysis")
        for row in rows:
            row["payload"] = json.loads(row["payload"])
            for ov in overrides.get(row["analysis_id"], []):
                row["payload"][ov["field"]] = json.loads(ov["new_value"])
                if ov["field"] == "relevant":
                    row["relevant"] = int(bool(json.loads(ov["new_value"])))
                row.setdefault("pm_overrides", []).append(ov)
        return rows

    def current_signals(self, include_synthetic: bool = True, valid_only: bool = True) -> list[dict]:
        sql = """SELECT s.*, r.source, r.platform, r.source_url, r.created_at AS source_date, r.is_synthetic
                 FROM signals s
                 JOIN analyses a ON a.analysis_id = s.analysis_id AND a.is_current = 1
                 JOIN records r ON r.record_id = s.record_id AND r.duplicate_of IS NULL
                 WHERE 1 = 1"""
        if valid_only:
            sql += " AND s.quote_valid = 1"
        if not include_synthetic:
            sql += " AND r.is_synthetic = 0"
        rejected = {o["target_id"] for o in self.q(
            "SELECT target_id, new_value FROM overrides WHERE target_type='signal' AND field='rejected'")
            if json.loads(o["new_value"])}
        relevant = {a["analysis_id"] for a in self.current_analyses(include_synthetic) if a["relevant"]}
        return [s for s in self.q(sql) if s["evidence_id"] not in rejected and s["analysis_id"] in relevant]

    def _overrides_by_target(self, target_type: str) -> dict[str, list[dict]]:
        out: dict[str, list[dict]] = {}
        for o in self.q("SELECT * FROM overrides WHERE target_type = ? ORDER BY override_id", (target_type,)):
            out.setdefault(o["target_id"], []).append(o)
        return out
