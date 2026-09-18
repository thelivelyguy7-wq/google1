"""Quantitative analysis (spec §20-§21, §25).

Rule: every rate is returned as {numerator, denominator, pct, denominator_definition,
scope, directional}. Counts are of distinct RECORDS unless stated otherwise, so one
verbose post cannot inflate a pattern. Only signals with validated quotes count.
"""
from __future__ import annotations

from collections import Counter, defaultdict

from . import taxonomy as tx
from .config import settings
from .store import Store

ATTEMPT_DEF = "records describing a first-person retrieval attempt (relevant, validated)"
RELEVANT_DEF = "records classified as relevant to photo retrieval"


def rate(n: int, d: int, definition: str, scope: dict) -> dict:
    return {
        "numerator": n, "denominator": d,
        "pct": round(100 * n / d, 1) if d else None,
        "denominator_definition": definition,
        "scope": scope["label"],
        "directional": d < settings.min_sample_for_percent,
    }


class Corpus:
    def __init__(self, store: Store, include_synthetic: bool = True, sources: list[str] | None = None,
                 dataset: str | None = None):
        self.store = store
        analyses = store.current_analyses(include_synthetic)
        if sources:
            analyses = [a for a in analyses if a["source"] in sources]
        if dataset:
            analyses = [a for a in analyses if a["dataset"] == dataset]
        self.analyses = analyses
        ids = {a["analysis_id"] for a in analyses}
        self.signals = [s for s in store.current_signals(include_synthetic) if s["analysis_id"] in ids]
        self.signals_by_analysis: dict[str, list[dict]] = defaultdict(list)
        for s in self.signals:
            self.signals_by_analysis[s["analysis_id"]].append(s)
        self.record_meta = {a["record_id"]: a for a in analyses}

        records = store.q("SELECT record_id, source, created_at, is_synthetic, duplicate_of, dataset FROM records")
        if sources:
            records = [r for r in records if r["source"] in sources]
        if dataset:
            records = [r for r in records if r["dataset"] == dataset]
        if not include_synthetic:
            records = [r for r in records if not r["is_synthetic"]]
        self.records = records
        dates = sorted(r["created_at"] for r in records if r["created_at"])
        srcs = Counter(r["source"] for r in records if not r["duplicate_of"])
        self.scope = {
            "label": f"{sum(srcs.values())} unique records from {len(srcs)} sources"
                     + (f", {dates[0][:10]} to {dates[-1][:10]}" if dates else "")
                     + (" (includes generated records)" if any(r["is_synthetic"] for r in records) and settings.provenance == "auto" else ""),
            "sources": dict(srcs),
            "date_range": [dates[0], dates[-1]] if dates else None,
            "synthetic_records": sum(1 for r in records if r["is_synthetic"]),
            "analyzers": dict(Counter(a["analyzer"] for a in analyses)),
        }

    # -- populations ----------------------------------------------------------
    @property
    def relevant(self) -> list[dict]:
        return [a for a in self.analyses if a["relevant"]]

    @property
    def attempts(self) -> list[dict]:
        return [a for a in self.relevant if a["payload"].get("describes_retrieval_attempt")]

    def evidence(self, s: dict) -> dict:
        return {k: s.get(k) for k in ("evidence_id", "record_id", "source", "platform", "source_url", "source_date",
                                      "kind", "label", "value", "quote", "is_synthetic")}

    # -- building blocks ---------------------------------------------------------
    def label_distribution(self, kind: str, population: list[dict], definition: str, examples: int = 3) -> list[dict]:
        pop_ids = {a["analysis_id"] for a in population}
        records_by_label: dict[str, set] = defaultdict(set)
        sources_by_label: dict[str, Counter] = defaultdict(Counter)
        ev_by_label: dict[str, list] = defaultdict(list)
        for s in self.signals:
            if s["kind"] != kind or s["analysis_id"] not in pop_ids:
                continue
            if s["record_id"] not in records_by_label[s["label"]]:
                sources_by_label[s["label"]][s["source"]] += 1
                ev_by_label[s["label"]].append(self.evidence(s))
            records_by_label[s["label"]].add(s["record_id"])
        d = len({a["record_id"] for a in population})
        rows = []
        for label, recs in records_by_label.items():
            rows.append({
                "label": label, **rate(len(recs), d, definition, self.scope),
                "source_count": len(sources_by_label[label]), "by_source": dict(sources_by_label[label]),
                "proposed": label.startswith("proposed:"),
                "examples": diverse_examples(ev_by_label[label], examples),
            })
        return sorted(rows, key=lambda r: -r["numerator"])

    def field_distribution(self, field: str, population: list[dict], definition: str) -> list[dict]:
        d = len({a["record_id"] for a in population})
        by_val: dict[str, set] = defaultdict(set)
        src: dict[str, Counter] = defaultdict(Counter)
        for a in population:
            v = a["payload"].get(field) or "unknown"
            if a["record_id"] not in by_val[v]:
                src[v][a["source"]] += 1
            by_val[v].add(a["record_id"])
        return sorted(
            [{"label": v, **rate(len(r), d, definition, self.scope), "source_count": len(src[v]), "by_source": dict(src[v])}
             for v, r in by_val.items()], key=lambda r: -r["numerator"])

    # -- dashboard sections ----------------------------------------------------------
    def overview(self) -> dict:
        unique = [r for r in self.records if not r["duplicate_of"]]
        attempts = self.attempts
        status = Counter(a["payload"].get("success_status") for a in attempts)
        total_q = sum(a["quotes_total"] or 0 for a in self.analyses)
        bad_q = sum(a["quotes_invalid"] or 0 for a in self.analyses)
        return {
            "scope": self.scope,
            "total_records": len(self.records),
            "unique_records": len(unique),
            "duplicates_excluded": len(self.records) - len(unique),
            "analyzed_chunks": len(self.analyses),
            "relevant": rate(len({a["record_id"] for a in self.relevant}), len({a["record_id"] for a in self.analyses}),
                             "analyzed unique records", self.scope),
            "retrieval_attempts": rate(len({a["record_id"] for a in attempts}), len({a["record_id"] for a in self.relevant}),
                                       RELEVANT_DEF, self.scope),
            "perspectives": dict(Counter(a["payload"].get("perspective") for a in self.relevant)),
            "outcomes": {k: rate(v, len(attempts), ATTEMPT_DEF, self.scope) for k, v in status.most_common()},
            "quote_validation": {"quotes_total": total_q, "quotes_invalid": bad_q,
                                 "invalid_pct": round(100 * bad_q / total_q, 1) if total_q else None},
            "proposed_labels": sorted({s["label"] for s in self.signals if s["label"].startswith("proposed:")}),
        }

    def scenarios(self) -> list[dict]:
        attempts = self.attempts
        rows = self.field_distribution("retrieval_scenario", attempts, ATTEMPT_DEF)
        for row in rows:
            pop = [a for a in attempts if a["payload"].get("retrieval_scenario") == row["label"]]
            n = len(pop)
            row["outcomes"] = {k: rate(v, n, f"attempts in scenario {row['label']}", self.scope)
                               for k, v in Counter(a["payload"].get("success_status") for a in pop).most_common()}
            row["failure_stages"] = {k: rate(v, n, f"attempts in scenario {row['label']}", self.scope)
                                     for k, v in Counter(a["payload"].get("failure_stage") for a in pop).most_common()}
            row["top_remembered"] = [(r["label"], r["numerator"]) for r in self.label_distribution("remembered", pop, "", 0)[:4]]
            row["top_forgotten"] = [(r["label"], r["numerator"]) for r in self.label_distribution("forgotten", pop, "", 0)[:4]]
            row["top_workarounds"] = [(r["label"], r["numerator"]) for r in self.label_distribution("workaround", pop, "", 0)[:4]]
        return rows

    def memory(self) -> list[dict]:
        rows = self.label_distribution("remembered", self.attempts, ATTEMPT_DEF)
        prec = defaultdict(Counter)
        for s in self.signals:
            if s["kind"] == "remembered":
                prec[s["label"]][s["precision"]] += 1
        for r in rows:
            r["precision"] = dict(prec[r["label"]])
        return rows

    def forgotten(self) -> list[dict]:
        """Forgotten information + association with failure (§14: does it actually create a barrier?)."""
        attempts = self.attempts
        rows = self.label_distribution("forgotten", attempts, ATTEMPT_DEF)
        failed = lambda a: a["payload"].get("success_status") in ("not_found", "abandoned", "partially_found", "uncertain")
        by_rec = defaultdict(set)
        for s in self.signals:
            if s["kind"] == "forgotten":
                by_rec[s["label"]].add(s["analysis_id"])
        for r in rows:
            with_ = [a for a in attempts if a["analysis_id"] in by_rec[r["label"]]]
            without = [a for a in attempts if a["analysis_id"] not in by_rec[r["label"]]]
            r["unsuccessful_when_forgotten"] = rate(sum(map(failed, with_)), len(with_), f"attempts where {r['label']}", self.scope)
            r["unsuccessful_when_not_forgotten"] = rate(sum(map(failed, without)), len(without), f"attempts without {r['label']}", self.scope)
            r["explicitly_blocks_retrieval"] = rate(
                sum(1 for a in with_ if a["payload"].get("forgotten_info_blocks_retrieval") == "yes"), len(with_),
                f"attempts where {r['label']}", self.scope)
            r["note"] = "Association only; not causal. 'explicitly_blocks_retrieval' counts texts that link the gap to the failure."
        return rows

    def search_formulation(self) -> dict:
        attempts = self.attempts
        ids = {a["analysis_id"] for a in attempts}
        queries = [s for s in self.signals if s["kind"] == "query" and s["analysis_id"] in ids]
        qd = len(queries)
        types = Counter(q["label"] for q in queries)
        orient = Counter()
        outcome_by_type = defaultdict(Counter)
        for q in queries:
            o, _, outcome = (q["precision"] or "|").partition("|")
            for x in filter(None, o.split(",")):
                orient[x] += 1
            outcome_by_type[q["label"]][outcome] += 1
        lengths = [len((q["value"] or "").split()) for q in queries if q["value"]]
        multi = sum(1 for a in attempts if (a["payload"].get("attempt_count") or 0) >= 2)
        return {
            "queries_extracted": qd,
            "attempts_with_quoted_query": rate(len({q["record_id"] for q in queries}), len(attempts), ATTEMPT_DEF, self.scope),
            "query_types": {k: rate(v, qd, "extracted queries", self.scope) for k, v in types.most_common()},
            "orientation": {k: rate(v, qd, "extracted queries (multi-label)", self.scope) for k, v in orient.most_common()},
            "outcome_by_query_type": {k: dict(v) for k, v in outcome_by_type.items()},
            "median_query_words": sorted(lengths)[len(lengths) // 2] if lengths else None,
            "multiple_attempts": rate(multi, len(attempts), ATTEMPT_DEF, self.scope),
            "strategies": self.label_distribution("strategy", attempts, ATTEMPT_DEF),
            "examples": diverse_examples([self.evidence(q) for q in queries], 8),
        }

    def failures(self) -> list[dict]:
        attempts = self.attempts
        rows = self.field_distribution("failure_stage", attempts, ATTEMPT_DEF)
        ev = defaultdict(list)
        for s in self.signals:
            if s["kind"] == "failure":
                ev[s["label"]].append(self.evidence(s))
        for r in rows:
            r["description"] = tx.FAILURE_STAGES.get(r["label"], "Proposed / unmapped stage")
            r["examples"] = diverse_examples(ev[r["label"]], 3)
        return rows

    def workarounds(self) -> list[dict]:
        return self.label_distribution("workaround", self.attempts, ATTEMPT_DEF)

    def segments_raw(self) -> list[dict]:
        return self.label_distribution("segment", self.relevant, RELEVANT_DEF)

    def crosstab(self, row_field: str, col_field: str) -> dict:
        table = defaultdict(Counter)
        for a in self.attempts:
            table[a["payload"].get(row_field) or "unknown"][a["payload"].get(col_field) or "unknown"] += 1
        cols = sorted({c for r in table.values() for c in r})
        return {"rows": sorted(table), "cols": cols, "cells": {r: dict(v) for r, v in table.items()},
                "unit": "attempt records", "scope": self.scope["label"]}

    def scenario_x_forgotten(self) -> dict:
        table = defaultdict(Counter)
        ids = {a["analysis_id"]: a for a in self.attempts}
        seen = set()
        for s in self.signals:
            if s["kind"] == "forgotten" and s["analysis_id"] in ids and (s["record_id"], s["label"]) not in seen:
                seen.add((s["record_id"], s["label"]))
                table[ids[s["analysis_id"]]["payload"].get("retrieval_scenario")][s["label"]] += 1
        cols = sorted({c for r in table.values() for c in r})
        return {"rows": sorted(table), "cols": cols, "cells": {r: dict(v) for r, v in table.items()},
                "unit": "attempt records", "scope": self.scope["label"]}

    def journey(self) -> list[dict]:
        attempts = self.attempts
        ids = {a["analysis_id"] for a in attempts}
        steps = defaultdict(list)
        for s in self.signals:
            if s["kind"] == "journey" and s["analysis_id"] in ids:
                steps[s["label"]].append(s)
        out = []
        for stage in tx.JOURNEY_STAGES + ["other"]:
            st = steps.get(stage, [])
            if not st and stage == "other":
                continue
            recs = {s["record_id"] for s in st}
            hard = {s["record_id"] for s in st if s["precision"] == "difficulty"}
            out.append({
                "stage": stage,
                "records_with_step": rate(len(recs), len(attempts), ATTEMPT_DEF, self.scope),
                "records_with_difficulty": rate(len(hard), len(attempts), ATTEMPT_DEF, self.scope),
                "examples": diverse_examples([self.evidence(s) for s in st if s["precision"] == "difficulty"], 3),
            })
        return out


def diverse_examples(items: list[dict], k: int) -> list[dict]:
    """Round-robin across sources so examples are not all from one platform (§36, §40)."""
    if k <= 0:
        return []
    by_src = defaultdict(list)
    for it in items:
        by_src[it.get("source")].append(it)
    out, seen_records = [], set()
    while len(out) < k and any(by_src.values()):
        for src in list(by_src):
            if not by_src[src]:
                continue
            it = by_src[src].pop(0)
            if it["record_id"] in seen_records:
                continue
            seen_records.add(it["record_id"])
            out.append(it)
            if len(out) >= k:
                break
    return out
