"""Evidence Validator (spec §10, §38 module 11, §41).

* A quote is valid only if it can be found verbatim (after whitespace / quote-mark
  normalisation) in the source text. Invalid quotes are kept for audit but
  excluded from every count.
* Labels outside the taxonomy become `proposed:<label>` rather than being silently
  forced into a category (§12, §15, §17).
"""
from __future__ import annotations

import hashlib
import re

from . import taxonomy as tx

_QUOTE_CHARS = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"', "–": "-", "—": "-"})


def _norm(s: str) -> str:
    s = (s or "").translate(_QUOTE_CHARS).lower()
    return re.sub(r"\s+", " ", s).strip()


def quote_is_valid(quote: str, source_text: str) -> bool:
    q = _norm(quote).strip(" .,!?;:\"'")
    if len(q) < 3:
        return False
    src = _norm(source_text)
    # Allow elided quotes ("a ... b"): each fragment must appear, in order.
    pos = 0
    for frag in [f.strip(" .,!?;:\"'") for f in re.split(r"\.\.\.|…", q)]:
        if not frag:
            continue
        idx = src.find(frag, pos)
        if idx < 0:
            return False
        pos = idx + len(frag)
    return True


VOCAB = {
    "remembered": set(tx.MEMORY_SIGNALS),
    "forgotten": set(tx.FORGOTTEN_INFORMATION),
    "behavior": set(tx.BEHAVIORS),
    "strategy": set(tx.BEHAVIORS),
    "refinement": set(tx.BEHAVIORS) | set(tx.WORKAROUNDS),
    "workaround": set(tx.WORKAROUNDS),
}
_PREFIX = {"remembered": "remembered_"}


def normalize_label(kind: str, label: str) -> str:
    label = re.sub(r"[^a-z0-9_:]+", "_", (label or "").strip().lower()).strip("_")
    vocab = VOCAB.get(kind)
    if vocab is None or label.startswith("proposed:"):
        return label or "unlabelled"
    if label in vocab:
        return label
    prefixed = _PREFIX.get(kind, "") + label
    if prefixed in vocab:
        return prefixed
    if kind == "forgotten" and f"{label}_unknown" in vocab:
        return f"{label}_unknown"
    return f"proposed:{label}"


def evidence_id(analysis_id: str, kind: str, idx: int) -> str:
    return "EV-" + hashlib.sha1(f"{analysis_id}|{kind}|{idx}".encode()).hexdigest()[:10]


SIGNAL_LISTS = {
    "remembered_information": "remembered",
    "forgotten_information": "forgotten",
    "search_strategies": "strategy",
    "query_refinements": "refinement",
    "user_behaviors": "behavior",
    "workarounds": "workaround",
    "expectations": "expectation",
    "segment_signals": "segment",
    "counter_evidence": "counter",
}


def validate_analysis(payload: dict, source_text: str, analysis_id: str, record_id: str) -> tuple[dict, list[dict], dict]:
    """Normalise labels in-place, flatten to signal rows, and report quote validity."""
    signals: list[dict] = []
    total = invalid = 0

    def add(kind: str, label: str, value: str, quote: str, precision: str | None):
        nonlocal total, invalid
        ok = quote_is_valid(quote, source_text)
        total += 1
        invalid += 0 if ok else 1
        signals.append({
            "evidence_id": evidence_id(analysis_id, kind, len(signals)),
            "analysis_id": analysis_id, "record_id": record_id, "kind": kind,
            "label": label, "value": value, "quote": quote, "quote_valid": int(ok), "precision": precision,
        })
        return ok

    for field, kind in SIGNAL_LISTS.items():
        for sig in payload.get(field) or []:
            sig["label"] = normalize_label(kind, sig.get("label", ""))
            sig["quote_valid"] = add(kind, sig["label"], sig.get("value", ""), sig.get("quote", ""), sig.get("precision"))

    for qa in payload.get("queries") or []:
        qa["quote_valid"] = add("query", qa.get("query_type", "unknown"), qa.get("query_text", ""), qa.get("quote", ""),
                                ",".join(qa.get("orientation") or []) + "|" + qa.get("outcome", ""))

    stage = payload.get("failure_stage") or "unclear"
    if stage not in tx.FAILURE_STAGES:
        stage = f"proposed:{normalize_label('failure', stage)}"
    payload["failure_stage"] = stage
    if stage not in ("none_observed",) and payload.get("failure_quote"):
        payload["failure_quote_valid"] = add("failure", stage, payload.get("failure_reason", ""), payload["failure_quote"], None)

    for step in payload.get("journey") or []:
        step["quote_valid"] = add("journey", step.get("stage", "other"), step.get("observation", ""), step.get("quote", ""),
                                  "difficulty" if step.get("difficulty") else "ok")

    scenario = payload.get("retrieval_scenario") or "other"
    scenario = normalize_label("scenario", scenario)
    if scenario not in tx.RETRIEVAL_SCENARIOS and not scenario.startswith("proposed:"):
        scenario = f"proposed:{scenario}"
    payload["retrieval_scenario"] = scenario

    payload["opportunity_areas"] = [
        a if (a in tx.SEED_OPPORTUNITY_AREAS or a.startswith("proposed:")) else f"proposed:{normalize_label('opp', a)}"
        for a in (payload.get("opportunity_areas") or [])
    ]
    report = {"quotes_total": total, "quotes_invalid": invalid}
    payload["validation"] = report
    return payload, signals, report
