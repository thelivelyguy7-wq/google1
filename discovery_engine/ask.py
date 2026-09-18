"""PM question interface (spec §35).

The question is turned into a *plan* (filters + intent). Answers are assembled
deterministically from the stored evidence, so an LLM never writes a number or
a quote. Claude, when available, only parses the question into the plan.
"""
from __future__ import annotations

import re
from typing import Literal, Optional

from pydantic import BaseModel

from . import taxonomy as tx
from .analyze.llm import claude_available
from .quant import Corpus
from .search import EvidenceIndex, Filters
from .synthesis import contradictions_for, opportunities, profile

Intent = Literal["find_evidence", "memory_distribution", "forgotten_distribution", "workaround_distribution",
                 "failure_distribution", "compare_scenarios", "cross_source_opportunities", "contradictions",
                 "hypotheses", "scenario_distribution", "search_formulation"]


class Plan(BaseModel):
    intent: Intent
    query_text: str
    remembered: list[str]
    forgotten: list[str]
    scenarios: list[str]
    compare_scenarios: list[str]
    success_status: list[str]
    failure_stages: list[str]
    workarounds: list[str]
    opportunity: Optional[str]
    attempts_only: bool


CLUE_WORDS = {
    "place": ("remembered_place", "exact_location_unknown"), "location": ("remembered_place", "exact_location_unknown"),
    "where": ("remembered_place", "exact_location_unknown"), "date": ("remembered_time_approximation", "exact_date_unknown"),
    "time": ("remembered_time_approximation", "exact_date_unknown"), "when": ("remembered_time_approximation", "exact_date_unknown"),
    "year": ("remembered_time_approximation", "exact_date_unknown"), "person": ("remembered_person", "person_name_unknown"),
    "name": ("remembered_person", "person_name_unknown"), "people": ("remembered_person", "person_name_unknown"),
    "event": ("remembered_event", "event_name_unknown"), "text": ("remembered_text", "exact_text_unknown"),
    "words": ("remembered_text", "exact_text_unknown"), "object": ("remembered_object", "exact_object_name_unknown"),
    "album": (None, "album_unknown"), "trip": ("remembered_trip", None), "context": ("remembered_context", None),
    "visual": ("remembered_visual_appearance", None), "looked": ("remembered_visual_appearance", None),
}
SCENARIO_WORDS = {
    "travel": "travel_memory", "trip": "travel_memory", "document": "document", "receipt": "receipt", "bill": "receipt",
    "screenshot": "screenshot", "wedding": "wedding_memory", "food": "food_restaurant_memory", "restaurant": "food_restaurant_memory",
    "medical": "medical_or_health_image", "health": "medical_or_health_image", "medicine": "medical_or_health_image",
    "video": "video", "family": "family_memory", "friend": "friend_memory", "event": "event_memory", "work": "work_memory",
    "purchase": "purchase_related_image", "product": "purchase_related_image", "school": "school_or_college_memory", "college": "school_or_college_memory",
}


def _clues(fragment: str, idx: int) -> list[str]:
    out = []
    for w, labels in CLUE_WORDS.items():
        if re.search(rf"\b{w}s?\b", fragment) and labels[idx]:
            out.append(labels[idx])
    return sorted(set(out))


def rule_plan(question: str) -> Plan:
    q = question.lower()
    plan = dict(intent="find_evidence", query_text=question, remembered=[], forgotten=[], scenarios=[], compare_scenarios=[],
                success_status=[], failure_stages=[], workarounds=[], opportunity=None, attempts_only=False)
    opp = next((o for o in tx.SEED_OPPORTUNITY_AREAS if o in q or o.replace("_", " ") in q), None)
    plan["opportunity"] = opp
    if "compare" in q:
        plan["intent"] = "compare_scenarios"
        plan["compare_scenarios"] = list(dict.fromkeys(v for k, v in SCENARIO_WORDS.items() if re.search(rf"\b{k}", q)))[:2]
    elif "contradict" in q or "challenge" in q:
        plan["intent"] = "contradictions"
    elif "hypothes" in q:
        plan["intent"] = "hypotheses"
    elif "opportunit" in q and ("multiple sources" in q or "across" in q):
        plan["intent"] = "cross_source_opportunities"
    elif "workaround" in q or "after search fail" in q:
        plan["intent"] = "workaround_distribution"
    elif "failure point" in q or ("fail" in q and "most" in q):
        plan["intent"] = "failure_distribution"
    elif re.search(r"\bforget|forgotten\b", q) and re.search(r"\b(what|which|most|commonly)\b", q) and "but" not in q:
        plan["intent"] = "forgotten_distribution"
    elif "remember" in q and re.search(r"\b(most|frequently|what information)\b", q) and "but" not in q:
        plan["intent"] = "memory_distribution"
    elif "formulat" in q or "how do users search" in q:
        plan["intent"] = "search_formulation"
    elif "what kinds" in q or "scenario" in q:
        plan["intent"] = "scenario_distribution"
    else:
        m = re.search(r"remember(?:ed)?(.*?)(?:\bbut\b|\bwithout\b)(.*)", q)
        if m:
            plan["remembered"], plan["forgotten"] = _clues(m.group(1), 0), _clues(m.group(2), 1)
        elif "remember" in q:
            plan["remembered"] = _clues(q.split("remember", 1)[1], 0)
        if "abandon" in q or "gave up" in q or "give up" in q:
            plan["success_status"] = ["abandoned"]
        plan["scenarios"] = list(dict.fromkeys(v for k, v in SCENARIO_WORDS.items() if re.search(rf"\b{k}", q)))
        if "event description" in q:
            plan["remembered"] = sorted(set(plan["remembered"]) | {"remembered_event"})
            plan["scenarios"] = []
        plan["attempts_only"] = "attempt" in q or "retrieval" in q
    return Plan(**plan)


def claude_plan(question: str) -> Plan:
    from .analyze.llm import ClaudeAnalyzer
    system = ("Convert a product manager's question about a photo-retrieval evidence database into a query plan. "
              f"Allowed remembered labels: {tx.MEMORY_SIGNALS}. Forgotten labels: {tx.FORGOTTEN_INFORMATION}. "
              f"Scenarios: {tx.RETRIEVAL_SCENARIOS}. Failure stages: {list(tx.FAILURE_STAGES)}. Workarounds: {tx.WORKAROUNDS}. "
              f"Success status: {tx.SUCCESS_STATUS}. Opportunities: {list(tx.SEED_OPPORTUNITY_AREAS)}. "
              "Use empty lists when the question does not constrain a field. Do not answer the question.")
    return ClaudeAnalyzer().complete_json(system, question, Plan, effort="low", max_tokens=4000)


def answer(store, question: str, use_claude: bool | None = None, k: int = 8, include_synthetic: bool = True) -> dict:
    plan = None
    if use_claude or (use_claude is None and claude_available()):
        try:
            plan = claude_plan(question)
        except Exception:
            plan = None
    plan = plan or rule_plan(question)
    c = Corpus(store, include_synthetic)
    result: dict = {"question": question, "plan": plan.model_dump(), "scope": c.scope,
                    "note": "Numbers and quotes are pulled straight from stored evidence; nothing is generated."}

    if plan.intent == "memory_distribution":
        result["table"] = c.memory()
    elif plan.intent == "forgotten_distribution":
        result["table"] = c.forgotten()
    elif plan.intent == "workaround_distribution":
        failed = [a for a in c.attempts if a["payload"].get("success_status") in ("not_found", "abandoned", "partially_found", "uncertain")
                  or a["payload"].get("failure_stage") not in ("none_observed", "unclear")]
        result["table"] = c.label_distribution("workaround", failed, "attempts with a failure or unsuccessful outcome")
    elif plan.intent == "failure_distribution":
        result["table"] = c.failures()
    elif plan.intent == "scenario_distribution":
        result["table"] = c.scenarios()
    elif plan.intent == "search_formulation":
        result["table"] = c.search_formulation()
    elif plan.intent == "compare_scenarios":
        result["comparison"] = {s: profile(c, [a for a in c.attempts if a["payload"].get("retrieval_scenario") == s], s)
                                for s in plan.compare_scenarios}
    elif plan.intent in ("cross_source_opportunities", "contradictions", "hypotheses"):
        opps = opportunities(c)
        if plan.intent == "cross_source_opportunities":
            result["table"] = [{k2: o[k2] for k2 in ("opportunity", "records", "unique_sources", "source_distribution", "evidence_strength")}
                               for o in opps if o["unique_sources"] >= 3]
        else:
            from .hypotheses import build_hypotheses, select_leading
            target = plan.opportunity or (select_leading(opps) or {}).get("leading")
            match = [o for o in opps if o["opportunity"] == target]
            result["opportunity"] = target
            if plan.intent == "contradictions" and match:
                sup = [a for a in c.relevant if a["record_id"] in set(match[0]["record_ids"])]
                result["contradictions"] = contradictions_for(c, sup, target)
            elif match:
                result["hypotheses"] = build_hypotheses(c, match, 1)
    else:
        f = Filters(remembered=plan.remembered, forgotten=plan.forgotten, scenarios=plan.scenarios,
                    success_status=plan.success_status, failure_stages=plan.failure_stages, workarounds=plan.workarounds,
                    opportunities=[plan.opportunity] if plan.opportunity else [], attempts_only=plan.attempts_only,
                    include_synthetic=include_synthetic)
        text_query = plan.query_text if not (plan.remembered or plan.forgotten or plan.success_status) else ""
        result["evidence"] = EvidenceIndex(store).search(text_query, f, k)
    return result
