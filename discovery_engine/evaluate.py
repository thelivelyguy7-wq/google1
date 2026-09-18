"""Score analyzer output against synthetic ground truth (Phase 9.4).

Scores show how well the extractor recovers what the generator intended.
On template-generated text they OVERSTATE real-world accuracy, especially for
the heuristic analyzer, whose lexicon is close to the templates' vocabulary.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from .store import Store


def _prf(tp: int, fp: int, fn: int) -> dict:
    p = tp / (tp + fp) if tp + fp else None
    r = tp / (tp + fn) if tp + fn else None
    f = 2 * p * r / (p + r) if p and r else None
    rnd = lambda x: round(x, 3) if x is not None else None
    return {"precision": rnd(p), "recall": rnd(r), "f1": rnd(f), "tp": tp, "fp": fp, "fn": fn}


def evaluate(store: Store, truth_path: str | Path) -> dict:
    truths = {t["record_id"]: t for t in map(json.loads, Path(truth_path).read_text(encoding="utf-8").splitlines())}
    analyses = {a["record_id"]: a for a in store.current_analyses(True)}
    valid = defaultdict(lambda: defaultdict(set))
    for s in store.q("SELECT s.* FROM signals s JOIN analyses a ON a.analysis_id = s.analysis_id AND a.is_current = 1 WHERE s.quote_valid = 1"):
        valid[s["record_id"]][s["kind"]].add(s["label"])

    out: dict = {"records_with_truth": len(truths), "records_analyzed": 0, "duplicates_not_analyzed": 0}
    binary = {"relevant": [0, 0, 0, 0], "attempt": [0, 0, 0, 0]}  # tp fp fn tn
    exact = defaultdict(lambda: [0, 0])  # correct, total
    multi = defaultdict(lambda: [0, 0, 0])
    confusion = defaultdict(lambda: defaultdict(int))

    for rid, t in truths.items():
        a = analyses.get(rid)
        if a is None:
            out["duplicates_not_analyzed"] += 1
            continue
        out["records_analyzed"] += 1
        p = a["payload"]
        for key, pred, gold in (("relevant", bool(a["relevant"]), t["relevant"]),
                                ("attempt", bool(p.get("describes_retrieval_attempt")) and bool(a["relevant"]), t.get("attempt", False))):
            idx = 0 if pred and gold else 1 if pred else 2 if gold else 3
            binary[key][idx] += 1
        if t.get("kind") != "attempt":
            continue
        for field, gold in (("retrieval_scenario", t["scenario"]), ("success_status", t["outcome"]), ("failure_stage", t["failure_stage"])):
            pred = p.get(field)
            exact[field][0] += int(pred == gold)
            exact[field][1] += 1
            if field == "failure_stage":
                confusion[gold][pred] += 1
        for kind, gold in (("remembered", t["remembered"]), ("forgotten", t["forgotten"]),
                           ("workaround", t["workarounds"]), ("segment", t["segments"])):
            pred = valid[rid][kind]
            g = set(gold)
            multi[kind][0] += len(pred & g)
            multi[kind][1] += len(pred - g)
            multi[kind][2] += len(g - pred)
        gold_q = {q["type"] for q in t["queries"]}
        pred_q = valid[rid]["query"]
        multi["query_type"][0] += len(pred_q & gold_q)
        multi["query_type"][1] += len(pred_q - gold_q)
        multi["query_type"][2] += len(gold_q - pred_q)

    out["binary"] = {k: {**_prf(v[0], v[1], v[2]), "accuracy": round((v[0] + v[3]) / max(1, sum(v)), 3)} for k, v in binary.items()}
    out["exact_match_on_attempts"] = {k: {"accuracy": round(c / n, 3) if n else None, "n": n} for k, (c, n) in exact.items()}
    out["multi_label_on_attempts"] = {k: _prf(*v) for k, v in multi.items()}
    out["failure_stage_confusion"] = {g: dict(v) for g, v in confusion.items()}
    out["analyzers"] = sorted({a["analyzer"] for a in analyses.values()})
    out["caveat"] = ("Scored against generator intent on template text. Scores overstate accuracy on real conversations; "
                     "a heuristic analyzer tuned on similar vocabulary especially so.")
    return out
