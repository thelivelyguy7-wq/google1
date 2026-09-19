"""FastAPI backend for the Discovery dashboard (spec §34, §35, §43, §44)."""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import taxonomy as tx
from .ask import answer
from .config import settings
from .report import build_bundle, render_brief, render_report
from .search import EvidenceIndex, Filters
from .store import Store

WEB = Path(__file__).parent / "web"
app = FastAPI(title="Discovery Engine")
store = Store(settings.db_path)
_index: EvidenceIndex | None = None


def index() -> EvidenceIndex:
    global _index
    if _index is None:
        _index = EvidenceIndex(store)
    return _index


def bundle(include_synthetic: bool = False) -> dict:
    # Defaults to the single ingested source per problemstatement.md §22: the old synthetic dataset
    # is still in the DB for anyone who deliberately asks for it, but it is not the default view.
    latest = store.latest_synthesis("discovery")
    if latest and latest["params"].get("include_synthetic", True) == include_synthetic:
        return latest["payload"]
    return build_bundle(store, include_synthetic)


app.mount("/static", StaticFiles(directory=WEB), name="static")


@app.get("/")
def home():
    return FileResponse(WEB / "index.html")


@app.get("/classic")
def classic():
    return FileResponse(WEB / "classic.html")


@app.get("/api/meta")
def meta():
    """Vocabularies for filters and challenge forms."""
    return {
        "journey_stages": tx.JOURNEY_STAGES,
        "scenarios": tx.RETRIEVAL_SCENARIOS,
        "memory_signals": tx.MEMORY_SIGNALS,
        "forgotten": tx.FORGOTTEN_INFORMATION,
        "behaviors": tx.BEHAVIORS,
        "workarounds": tx.WORKAROUNDS,
        "failure_stages": tx.FAILURE_STAGES,
        "success_status": tx.SUCCESS_STATUS,
        "perspectives": ["first_person_experience", "second_hand_report", "advice_or_answer", "opinion_or_feature_request", "other"],
        "opportunities": tx.SEED_OPPORTUNITY_AREAS,
        "sources": [r["source"] for r in store.q("SELECT DISTINCT source FROM records ORDER BY source")],
    }


@app.get("/api/review")
def review():
    """Items that most need PM attention: low-confidence or unclear analyses, proposed labels, failed quotes, change log."""
    texts = {r["chunk_id"]: r["text"] for r in store.q("SELECT chunk_id, text FROM chunks")}
    analyses = store.current_analyses(True)
    needs = []
    for a in analyses:
        if not a["relevant"]:
            continue
        p = a["payload"]
        reasons = []
        if (a["confidence"] or 0) < 0.45:
            reasons.append("low confidence")
        if p.get("failure_stage") == "unclear":
            reasons.append("failure stage unclear")
        if p.get("retrieval_scenario") in ("other",) or str(p.get("retrieval_scenario", "")).startswith("proposed:"):
            reasons.append("scenario not classified")
        if p.get("describes_retrieval_attempt") and p.get("success_status") == "not_stated":
            reasons.append("outcome not stated")
        if reasons:
            needs.append({"record_id": a["record_id"], "analysis_id": a["analysis_id"], "source": a["source"],
                          "confidence": a["confidence"], "reasons": reasons, "text": texts.get(a["chunk_id"], "")[:280],
                          "scenario": p.get("retrieval_scenario"), "failure_stage": p.get("failure_stage"),
                          "success_status": p.get("success_status"), "perspective": p.get("perspective"),
                          "has_override": bool(a.get("pm_overrides"))})
    needs.sort(key=lambda x: (-len(x["reasons"]), x["confidence"] or 0))
    proposed: dict[str, dict] = {}
    for s in store.current_signals(True):
        if s["label"].startswith("proposed:"):
            item = proposed.setdefault(s["label"], {"label": s["label"], "kind": s["kind"], "records": set(), "examples": []})
            item["records"].add(s["record_id"])
            if len(item["examples"]) < 3:
                item["examples"].append({k: s[k] for k in ("evidence_id", "record_id", "source", "quote")})
    invalid = store.q("""SELECT s.evidence_id, s.record_id, s.kind, s.label, s.quote, r.source FROM signals s
                         JOIN analyses a ON a.analysis_id = s.analysis_id AND a.is_current = 1
                         JOIN records r ON r.record_id = s.record_id
                         WHERE s.quote_valid = 0 LIMIT 100""")
    return {
        "needs_review": needs[:150],
        "needs_review_total": len(needs),
        "proposed_labels": [{**v, "records": len(v["records"])} for v in sorted(proposed.values(), key=lambda v: -len(v["records"]))],
        "invalid_quotes": invalid,
        "overrides": store.q("SELECT * FROM overrides ORDER BY override_id DESC LIMIT 200"),
    }


@app.get("/api/bundle")
def get_bundle(include_synthetic: bool = False):
    return bundle(include_synthetic)


@app.post("/api/rebuild")
def rebuild(include_synthetic: bool = False):
    global _index
    _index = None
    return build_bundle(store, include_synthetic)


@app.get("/api/record/{record_id:path}")
def record(record_id: str):
    rows = store.q("SELECT * FROM records WHERE record_id = ?", (record_id,))
    if not rows:
        raise HTTPException(404, "record not found")
    rec = rows[0]
    rec["replies"] = json.loads(rec["replies"] or "[]")
    rec["engagement"] = json.loads(rec["engagement"] or "{}")
    analyses = [a for a in store.current_analyses(True) if a["record_id"] == record_id]
    signals = store.q("SELECT * FROM signals WHERE record_id = ? AND analysis_id IN (SELECT analysis_id FROM analyses WHERE is_current = 1)", (record_id,))
    overrides = store.q("SELECT * FROM overrides WHERE target_id = ? OR target_id IN (SELECT evidence_id FROM signals WHERE record_id = ?)", (
        analyses[0]["analysis_id"] if analyses else "", record_id))
    history = store.q("SELECT analysis_id, analyzer, model, prompt_version, created_at, is_current FROM analyses WHERE record_id = ? ORDER BY created_at", (record_id,))
    return {"raw_evidence": rec, "ai_interpretation": analyses, "signals": signals, "overrides": overrides, "analysis_history": history}


class SearchBody(BaseModel):
    query: str = ""
    filters: dict = {}
    k: int = 12


@app.post("/api/search")
def search(body: SearchBody):
    return index().search(body.query, Filters.from_dict(body.filters), body.k)


class AskBody(BaseModel):
    question: str
    include_synthetic: bool = False


@app.post("/api/ask")
def ask(body: AskBody):
    return answer(store, body.question, include_synthetic=body.include_synthetic)


class OverrideBody(BaseModel):
    target_type: str            # "analysis" | "signal"
    target_id: str
    field: str                  # e.g. relevant, retrieval_scenario, failure_stage, success_status, rejected
    new_value: object
    note: str = ""


EDITABLE = {"analysis": {"relevant", "retrieval_scenario", "failure_stage", "success_status", "perspective",
                         "describes_retrieval_attempt", "opportunity_areas"},
            "signal": {"rejected"},
            "study": {"target_segment", "target_scenario_cluster", "target_opportunity"}}  # the PM's choice of segment(s) and opportunity


@app.post("/api/override")
def override(body: OverrideBody):
    global _index
    if body.field not in EDITABLE.get(body.target_type, set()):
        raise HTTPException(400, f"field {body.field} is not editable for {body.target_type}")
    old = None
    if body.target_type == "study":
        if body.field == "target_segment":
            old = store.selected_target_segment()
            note_msg = "Target segment recorded. Rebuild to refresh the research plan and problem definition."
        elif body.field == "target_scenario_cluster":
            old = store.selected_target_scenario_cluster()
            note_msg = "Target scenario cluster recorded. Rebuild to refresh the research plan and problem definition."
        elif body.field == "target_opportunity":
            old = store.selected_target_opportunity()
            note_msg = "Target opportunity recorded. Rebuild to refresh discovery focus, hypotheses, and brief."
        else:
            note_msg = "Selection recorded. Rebuild to refresh."
        store.add_override("study", "research", body.field, old, body.new_value, body.note)
        _index = None
        return {"ok": True, "note": note_msg}
    if body.target_type == "analysis":
        rows = store.q("SELECT payload FROM analyses WHERE analysis_id = ?", (body.target_id,))
        if not rows:
            raise HTTPException(404, "analysis not found")
        old = json.loads(rows[0]["payload"]).get(body.field)
    store.add_override(body.target_type, body.target_id, body.field, old, body.new_value, body.note)
    _index = None
    return {"ok": True, "note": "Override stored; the original AI output is kept. Rebuild to refresh aggregates."}


@app.get("/api/report.md", response_class=PlainTextResponse)
def report_md(include_synthetic: bool = False):
    return render_report(bundle(include_synthetic))


@app.get("/api/brief.md", response_class=PlainTextResponse)
def brief_md(include_synthetic: bool = False):
    return render_brief(bundle(include_synthetic))
