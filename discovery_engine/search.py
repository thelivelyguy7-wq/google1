"""Hybrid evidence retrieval (spec §35-§37).

TF-IDF semantic-ish relevance + structured filters, then MMR re-ranking with
explicit source and thread diversity penalties so answers are not dominated by
one platform or one thread. Swap `vectorize` for an embedding model if desired.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .store import Store


@dataclass
class Filters:
    sources: list[str] = field(default_factory=list)
    scenarios: list[str] = field(default_factory=list)
    failure_stages: list[str] = field(default_factory=list)
    success_status: list[str] = field(default_factory=list)
    perspectives: list[str] = field(default_factory=list)
    remembered: list[str] = field(default_factory=list)     # all must be present
    forgotten: list[str] = field(default_factory=list)      # all must be present
    workarounds: list[str] = field(default_factory=list)    # any
    behaviors: list[str] = field(default_factory=list)      # any
    opportunities: list[str] = field(default_factory=list)  # any
    record_ids: list[str] = field(default_factory=list)     # any: a precomputed set, e.g. one behavioural segment
    attempts_only: bool = False
    include_synthetic: bool = True
    date_from: str | None = None
    date_to: str | None = None

    @classmethod
    def from_dict(cls, d: dict | None) -> "Filters":
        d = d or {}
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__ and v not in (None, "")})


class EvidenceIndex:
    def __init__(self, store: Store):
        self.store = store
        self.docs = store.q(
            """SELECT a.analysis_id, a.record_id, a.payload, a.relevant, c.text, r.title, r.source, r.platform,
                      r.source_url, r.created_at, r.is_synthetic, r.thread_context
               FROM analyses a JOIN chunks c ON c.chunk_id = a.chunk_id JOIN records r ON r.record_id = a.record_id
               WHERE a.is_current = 1 AND r.duplicate_of IS NULL""")
        import json
        overrides = store._overrides_by_target("analysis")
        valid_signals = {}
        for s in store.current_signals(True):
            valid_signals.setdefault(s["analysis_id"], []).append(s)
        for d in self.docs:
            d["payload"] = json.loads(d["payload"])
            for ov in overrides.get(d["analysis_id"], []):
                d["payload"][ov["field"]] = json.loads(ov["new_value"])
            d["signals"] = valid_signals.get(d["analysis_id"], [])
            d["labels"] = {(s["kind"], s["label"]) for s in d["signals"]}
        corpus = [f"{d['title'] or ''} {d['text']}" for d in self.docs]
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=1, stop_words="english")
        self.matrix = self.vectorizer.fit_transform(corpus) if corpus else None

    def _passes(self, d: dict, f: Filters) -> bool:
        p = d["payload"]
        if not p.get("relevant"):
            return False
        if not f.include_synthetic and d["is_synthetic"]:
            return False
        checks = [
            (f.sources, lambda: d["source"] in f.sources),
            (f.scenarios, lambda: p.get("retrieval_scenario") in f.scenarios),
            (f.failure_stages, lambda: p.get("failure_stage") in f.failure_stages),
            (f.success_status, lambda: p.get("success_status") in f.success_status),
            (f.perspectives, lambda: p.get("perspective") in f.perspectives),
            (f.remembered, lambda: all(("remembered", l) in d["labels"] for l in f.remembered)),
            (f.forgotten, lambda: all(("forgotten", l) in d["labels"] for l in f.forgotten)),
            (f.workarounds, lambda: any(("workaround", l) in d["labels"] for l in f.workarounds)),
            (f.behaviors, lambda: any((k, l) in d["labels"] for l in f.behaviors for k in ("behavior", "strategy"))),
            (f.opportunities, lambda: bool(set(p.get("opportunity_areas") or []) & set(f.opportunities))),
            (f.record_ids, lambda: d["record_id"] in f.record_ids),
        ]
        if f.attempts_only and not p.get("describes_retrieval_attempt"):
            return False
        if f.date_from and (d["created_at"] or "") < f.date_from:
            return False
        if f.date_to and (d["created_at"] or "9999") > f.date_to:
            return False
        return all(fn() for cond, fn in checks if cond)

    def search(self, query: str = "", filters: Filters | None = None, k: int = 10, lam: float = 0.7,
               source_penalty: float = 0.15, thread_penalty: float = 0.2) -> dict:
        f = filters or Filters()
        idx = [i for i, d in enumerate(self.docs) if self._passes(d, f)]
        if not idx:
            return {"total_matches": 0, "results": [], "source_distribution": {}}
        sub = self.matrix[idx]
        if query.strip():
            rel = cosine_similarity(self.vectorizer.transform([query]), sub).ravel()
        else:
            rel = np.array([float(self.docs[i]["payload"].get("confidence") or 0.5) for i in idx])
        sim = cosine_similarity(sub)
        selected: list[int] = []
        src_count, thread_count = Counter(), Counter()
        candidates = list(range(len(idx)))
        while candidates and len(selected) < k:
            best, best_score = None, -1e9
            for j in candidates:
                d = self.docs[idx[j]]
                redundancy = max((sim[j, s] for s in selected), default=0.0)
                score = (lam * rel[j] - (1 - lam) * redundancy
                         - source_penalty * src_count[d["source"]]
                         - thread_penalty * (thread_count[d["thread_context"]] if d["thread_context"] else 0))
                if score > best_score:
                    best, best_score = j, score
            selected.append(best)
            candidates.remove(best)
            d = self.docs[idx[best]]
            src_count[d["source"]] += 1
            if d["thread_context"]:
                thread_count[d["thread_context"]] += 1
        results = []
        for j in selected:
            d = self.docs[idx[j]]
            p = d["payload"]
            results.append({
                "record_id": d["record_id"], "analysis_id": d["analysis_id"], "source": d["source"], "platform": d["platform"],
                "source_url": d["source_url"], "date": d["created_at"], "is_synthetic": bool(d["is_synthetic"]),
                "title": d["title"], "text": d["text"], "relevance": round(float(rel[j]), 3),
                "scenario": p.get("retrieval_scenario"), "success_status": p.get("success_status"),
                "failure_stage": p.get("failure_stage"), "perspective": p.get("perspective"),
                "opportunity_areas": p.get("opportunity_areas"),
                "signals": [{k2: s[k2] for k2 in ("evidence_id", "kind", "label", "value", "quote")} for s in d["signals"]],
            })
        all_src = Counter(self.docs[i]["source"] for i in idx)
        return {"total_matches": len(idx), "source_distribution": dict(all_src), "results": results}
