"""Segments, opportunity comparison, contradictions, root-cause chains (spec §18, §22-§29).

No hidden composite score: every comparison dimension is returned separately
and the UI lets the PM sort by any of them.
"""
from __future__ import annotations

from collections import Counter, defaultdict

from . import behavior_segments as bs
from . import taxonomy as tx
from .evidence import strength
from .labels import counts_phrase, readable, readable_list
from .quant import ATTEMPT_DEF, Corpus, diverse_examples, rate

UNSUCCESSFUL = ("not_found", "abandoned", "partially_found", "uncertain")

SCENARIO_SEGMENTS = {
    "Document, receipt & health-record retrievers": ["document", "receipt", "medical_or_health_image"],
    "Screenshot & purchase-reference retrievers": ["screenshot", "purchase_related_image"],
    "Experience-memory retrievers (travel, food, events, weddings)": ["travel_memory", "food_restaurant_memory", "event_memory", "wedding_memory"],
    "People-memory retrievers (family, friends, school)": ["family_memory", "friend_memory", "school_or_college_memory", "personal_memory"],
    "Place & object retrievers": ["location_memory", "object_memory", "work_memory"],
    "Video retrievers": ["video"],
}


def _is_vague(c: Corpus, a: dict) -> bool:
    kinds = {s["kind"] for s in c.signals_by_analysis[a["analysis_id"]]}
    return "remembered" in kinds and "forgotten" in kinds


def _labels(c: Corpus, a: dict, kind: str) -> set[str]:
    return {s["label"] for s in c.signals_by_analysis[a["analysis_id"]] if s["kind"] == kind}


def _tvd(p: Counter, q: Counter) -> float:
    ps, qs = sum(p.values()) or 1, sum(q.values()) or 1
    return round(0.5 * sum(abs(p[k] / ps - q[k] / qs) for k in set(p) | set(q)), 2)


def profile(c: Corpus, pop: list[dict], name: str) -> dict:
    """Shared descriptive profile for a population of analyses (segment or opportunity)."""
    n = len({a["record_id"] for a in pop})
    status = Counter(a["payload"].get("success_status") for a in pop)
    stages = Counter(a["payload"].get("failure_stage") for a in pop)
    sources = Counter(a["source"] for a in pop)
    attempts = [a for a in pop if a["payload"].get("describes_retrieval_attempt")]
    abandon = sum(1 for a in pop if a["payload"].get("success_status") == "abandoned" or "abandonment" in _labels(c, a, "workaround"))
    repeated = sum(1 for a in pop if (a["payload"].get("attempt_count") or 0) >= 2 or "repeated_search" in _labels(c, a, "strategy"))
    workarounds = Counter(l for a in pop for l in _labels(c, a, "workaround"))
    remembered = Counter(l for a in pop for l in _labels(c, a, "remembered"))
    forgotten = Counter(l for a in pop for l in _labels(c, a, "forgotten"))
    segments = Counter(l for a in pop for l in _labels(c, a, "segment"))
    top_stage = next(((k, v) for k, v in stages.most_common() if k not in ("none_observed", "unclear")), (None, 0))
    failing = sum(v for k, v in stages.items() if k not in ("none_observed", "unclear"))
    definition = f"records in '{name}'"
    return {
        "records": n,
        "unique_sources": len(sources),
        "source_distribution": dict(sources),
        "max_single_source_share": round(max(sources.values()) / n, 2) if n else None,
        "first_person_attempts": len(attempts),
        "vague_memory_cases": rate(sum(1 for a in pop if _is_vague(c, a)), n, definition, c.scope),
        "unsuccessful": rate(sum(status[s] for s in UNSUCCESSFUL), n, definition, c.scope),
        "abandonment_signals": rate(abandon, n, definition, c.scope),
        "repeated_search_signals": rate(repeated, n, definition, c.scope),
        "outcomes": dict(status),
        "failure_stages": dict(stages),
        "dominant_failure_stage": top_stage[0],
        "failure_concentration": round(top_stage[1] / failing, 2) if failing else None,
        "top_remembered": remembered.most_common(5),
        "top_forgotten": forgotten.most_common(5),
        "top_workarounds": workarounds.most_common(5),
        "segment_signals": segments.most_common(5),
        "scenarios": Counter(a["payload"].get("retrieval_scenario") for a in pop).most_common(),
        "synthetic_share": round(sum(1 for a in pop if a["is_synthetic"]) / len(pop), 2) if pop else 0,
    }


# ---------------------------------------------------------------------------
def segments(c: Corpus) -> tuple[list[dict], dict]:
    """The two primary retrieval segments (Direct, Contextual), plus the overview that explains the split.

    Returns (segments, overview). The primary cut is binary and exhaustive - every attempt is Direct or
    Contextual, so the shares always sum to 100%. The overview carries that partition plus the three
    secondary lenses (memory state, retrieval complexity, retrieval state) that characterize the attempts
    within each segment, rather than adding more primary segments.
    """
    cls = bs.classify(c)
    attempts = c.attempts
    n = len(cls)
    overall_stages = Counter(a["payload"].get("failure_stage") for a in attempts)
    by_primary: dict[str, list[dict]] = defaultdict(list)
    for v in cls.values():
        by_primary[v["primary"]].append(v)

    out = []
    for key in bs.ORDER:
        members = by_primary.get(key, [])
        if not members:
            continue
        pop = [v["analysis"] for v in members]
        name = bs.NAME[key]
        prof = profile(c, pop, name)
        prof["record_ids"] = sorted(v["analysis"]["record_id"] for v in members)
        contradicting = sum(1 for a in pop if _labels(c, a, "counter"))
        definition = f"attempts in '{name}'"
        # The signals that put each attempt here: the behaviour in the user's own words.
        # One quote per wording: identical sentences from different records say nothing new twice.
        seen, defining = set(), []
        for v in members:
            for s in v["flags"]["triggers"][key]:
                q = " ".join((s.get("quote") or "").lower().split())
                if q and q not in seen:
                    seen.add(q)
                    defining.append(c.evidence(s))
        routes = Counter(s["label"] for v in members for s in v["flags"]["triggers"]["recovery"] if s["kind"] == "workaround")
        retrieval_states = Counter(v["secondary"]["retrieval_state"] for v in members)
        prof.update({
            "segment": name, "key": key, "dimension": "behavioral", "number": bs.ORDER.index(key) + 1,
            "definition": bs.DEFINITION[key], "rule": bs.RULES[key], "journey_stages": bs.STAGES[key],
            "share_of_attempts": rate(prof["records"], n, ATTEMPT_DEF, c.scope),
            "found": rate(sum(1 for a in pop if a["payload"].get("success_status") == "found"), prof["records"], definition, c.scope),
            "retrieval_states": {k: rate(retrieval_states.get(k, 0), prof["records"], definition, c.scope) for k in bs.LENSES["retrieval_state"]["order"]},
            "recovery_routes": routes.most_common(6),
            "distinctiveness_vs_all_attempts": _tvd(Counter(a["payload"].get("failure_stage") for a in pop), overall_stages),
            "evidence_strength": strength(prof["records"], prof["unique_sources"],
                                          prof["first_person_attempts"] / prof["records"] if prof["records"] else 0,
                                          contradicting, prof["synthetic_share"]),
            "feasibility_of_primary_research": "PM judgement: can 5-6 people with this behaviour be recruited within the study timeline?",
            "potential_for_intervention": "PM judgement: is the dominant breakdown within product control, or a data/index limitation?",
            "defining_evidence": diverse_examples(defining, 4),
            "examples": diverse_examples([c.evidence(s) for a in pop for s in c.signals_by_analysis[a["analysis_id"]]
                                          if s["kind"] in ("failure", "forgotten")], 4),
        })
        out.append(prof)

    overview = {
        "attempts": n,
        "partition": [{"key": k, "name": bs.NAME[k], "rate": rate(len(by_primary.get(k, [])), n, ATTEMPT_DEF, c.scope)}
                      for k in bs.ORDER],
        "rules": bs.RULES,
        "precedence": bs.PRECEDENCE,
        "names": {k: bs.NAME[k] for k in bs.ORDER},
        "definitions": {k: bs.DEFINITION[k] for k in bs.ORDER},
        "target_segment_hypothesis": bs.TARGET_SEGMENT_HYPOTHESIS,
        "impact_map": bs.IMPACT_MAP,
        "note_on_direct": ("Public posts are written mostly when something goes wrong, so effortless retrievals are "
                           "under-represented here and hard ones over-represented. Direct Retrieval is the success path the metric "
                           "is aiming for; treat its small share as a property of the corpus, not of users. Recruit one Direct "
                           "participant deliberately as a contrast."),
        "secondary": _secondary_lenses(c, cls, n),
    }
    return out, overview


def _secondary_lenses(c: Corpus, cls: dict[str, dict], n: int) -> dict:
    """Memory state, retrieval complexity and outcome/effort: each across all attempts and within each primary segment."""
    lenses = {}
    for lens, meta in bs.LENSES.items():
        cats = []
        for cat in meta["order"]:
            members = [v for v in cls.values() if v["secondary"][lens] == cat]
            m = len(members)
            label = meta["labels"][cat]
            # Find rates use only attempts that say how they ended: posts about a deleted or unsynced photo often
            # state no outcome, and counting them as failures would blame the memory state for missing data.
            stated = [v for v in members if v["analysis"]["payload"].get("success_status") not in (None, "not_stated")]
            status = lambda v: v["analysis"]["payload"].get("success_status")
            cats.append({
                "key": cat, "label": label, "definition": meta["definitions"][cat],
                "rate": rate(m, n, ATTEMPT_DEF, c.scope),
                "found": rate(sum(1 for v in stated if status(v) == "found"), len(stated),
                              f"attempts with a stated outcome, {meta['name'].lower()} '{label}'", c.scope),
                "gave_up": rate(sum(1 for v in stated if status(v) == "abandoned"), len(stated),
                                f"attempts with a stated outcome, {meta['name'].lower()} '{label}'", c.scope),
                # How often the photo was simply not there to find: missing, unindexed, deleted or in another account.
                "data_missing": rate(sum(1 for v in members if v["analysis"]["payload"].get("failure_stage") == "F_data_index_limitation"),
                                     m, f"attempts with {meta['name'].lower()} '{label}'", c.scope),
                "record_ids": sorted(v["analysis"]["record_id"] for v in members),
            })
        by_segment = {}
        for key in bs.ORDER:
            seg = [v for v in cls.values() if v["primary"] == key]
            by_segment[key] = {cat: rate(sum(1 for v in seg if v["secondary"][lens] == cat), len(seg),
                                         f"attempts in '{bs.NAME[key]}'", c.scope) for cat in meta["order"]}
        lenses[lens] = {"name": meta["name"], "question": meta["question"], "rule": meta["rule"],
                        "order": meta["order"], "categories": cats, "by_segment": by_segment}
    return lenses


def retrieval_state_profiles(c: Corpus) -> list[dict]:
    """Full profiles for the five Retrieval State categories, for research fit and the report.

    Unlike the primary segments, these are not exclusive user groups: they describe how an attempt
    (mostly a Contextual one) actually played out. Built the same way as segment profiles so they can
    be compared on the same dimensions (evidence strength, sources, outcomes).
    """
    cls = bs.classify(c)
    n = len(cls)
    meta = bs.LENSES["retrieval_state"]
    by_state: dict[str, list[dict]] = defaultdict(list)
    for v in cls.values():
        by_state[v["secondary"]["retrieval_state"]].append(v)

    out = []
    for key in meta["order"]:
        members = by_state.get(key, [])
        if not members:
            continue
        pop = [v["analysis"] for v in members]
        label = meta["labels"][key]
        prof = profile(c, pop, label)
        prof["record_ids"] = sorted(v["analysis"]["record_id"] for v in members)
        contradicting = sum(1 for a in pop if _labels(c, a, "counter"))
        prof.update({
            "state": label, "key": key, "definition": meta["definitions"][key],
            "share_of_attempts": rate(prof["records"], n, ATTEMPT_DEF, c.scope),
            "primary_mix": Counter(v["primary"] for v in members).most_common(),
            "evidence_strength": strength(prof["records"], prof["unique_sources"],
                                          prof["first_person_attempts"] / prof["records"] if prof["records"] else 0,
                                          contradicting, prof["synthetic_share"]),
        })
        out.append(prof)
    return out


# ---------------------------------------------------------------------------
# Which counter-evidence labels refute which opportunity. Exposed so the PM can challenge it:
# e.g. "it was in my partner's library" refutes a search-understanding barrier but SUPPORTS index_coverage_gaps.
SEARCH_BARRIER_OPPS = {"context_to_query_translation", "approximate_time_anchoring", "multi_clue_combination",
                       "candidate_recognition", "recovery_after_failed_search", "text_in_image_recall"}
COUNTER_CONTRADICTS = {
    "vague_search_succeeded": SEARCH_BARRIER_OPPS | {"trust_in_search_completeness"},
    "failure_not_search_related": SEARCH_BARRIER_OPPS,
}
# Types counted in the evidence-strength contradiction ratio. The others are reported but bound
# frequency/severity or generalisability rather than refuting that the barrier exists.
REFUTING_TYPES = {"explicit_counter_evidence"}


def contradictions_for(c: Corpus, supporting: list[dict], opp: str) -> list[dict]:
    scenarios = {a["payload"].get("retrieval_scenario") for a in supporting}
    sup_ids = {a["analysis_id"] for a in supporting}
    same_scen = [a for a in c.relevant if a["payload"].get("retrieval_scenario") in scenarios and a["analysis_id"] not in sup_ids]
    items = []

    counter = [s for a in same_scen + supporting for s in c.signals_by_analysis[a["analysis_id"]]
               if s["kind"] == "counter" and (opp in COUNTER_CONTRADICTS.get(s["label"], set()) or s["label"].startswith("proposed:"))]
    if counter:
        # Weight each refuting record by how concentrated the opportunity is in that record's scenario,
        # so broad opportunities are not all refuted by the same corpus-wide counter-evidence.
        sup_scen = Counter(a["payload"].get("retrieval_scenario") for a in supporting)
        top = max(sup_scen.values())
        scen_of = {a["record_id"]: a["payload"].get("retrieval_scenario") for a in same_scen + supporting}
        counter_records = {s["record_id"] for s in counter}
        weighted = round(sum(sup_scen.get(scen_of[r], 0) / top for r in counter_records), 1)
        items.append({"type": "explicit_counter_evidence",
                      "description": "Users in the same scenarios describe the opposite experience, or a cause that would not be addressed by this opportunity "
                                     f"(labels: {', '.join(sorted({s['label'] for s in counter}))}). "
                                     f"Scenario-weighted count: {weighted} (weight = the opportunity's record count in that scenario / its largest scenario count).",
                      "records": len(counter_records),
                      "weighted_records": weighted,
                      "evidence": diverse_examples([c.evidence(s) for s in counter], 4)})

    vague_success = [a for a in same_scen if a["payload"].get("describes_retrieval_attempt") and _is_vague(c, a)
                     and a["payload"].get("success_status") == "found" and a["payload"].get("failure_stage") in ("none_observed", "unclear")]
    if vague_success:
        items.append({"type": "vague_memory_success",
                      "description": "Attempts with incomplete memory that succeeded without a reported breakdown. Incomplete memory alone does not guarantee failure, which limits how often this barrier occurs.",
                      "records": len(vague_success),
                      "evidence": diverse_examples([c.evidence(s) for a in vague_success for s in c.signals_by_analysis[a["analysis_id"]]
                                                    if s["kind"] in ("forgotten", "behavior")], 4)})

    if opp != "index_coverage_gaps":
        alt = [a for a in supporting if a["payload"].get("failure_stage") == "F_data_index_limitation"]
        if alt:
            items.append({"type": "alternative_explanation",
                          "description": "Some supporting records attribute the failure to missing or unindexed data rather than to the user's memory or the query.",
                          "records": len(alt),
                          "evidence": diverse_examples([c.evidence(s) for a in alt for s in c.signals_by_analysis[a["analysis_id"]] if s["kind"] == "failure"], 3)})

    prof_sources = Counter(a["source"] for a in supporting)
    if supporting and max(prof_sources.values()) / len(supporting) > 0.5:
        src, v = prof_sources.most_common(1)[0]
        items.append({"type": "source_concentration",
                      "description": f"{v} of {len(supporting)} supporting records come from {src}; the pattern may be platform-specific.",
                      "records": v, "evidence": []})
    scen = Counter(a["payload"].get("retrieval_scenario") for a in supporting)
    if supporting and max(scen.values()) / len(supporting) > 0.6:
        s, v = scen.most_common(1)[0]
        items.append({"type": "scenario_concentration",
                      "description": f"{v} of {len(supporting)} supporting records are '{s}'; the pattern may not generalise to other retrieval scenarios.",
                      "records": v, "evidence": []})
    advice = [a for a in same_scen if a["payload"].get("perspective") == "advice_or_answer"]
    if advice:
        items.append({"type": "known_workaround_exists",
                      "description": "Other users recommend strategies for these scenarios; the barrier may be discoverability of existing capabilities rather than capability.",
                      "records": len(advice),
                      "evidence": diverse_examples([{"evidence_id": None, "record_id": a["record_id"], "source": a["source"], "platform": a["platform"],
                                                     "source_url": a["source_url"], "source_date": a["source_date"], "kind": "advice",
                                                     "label": "advice", "value": "", "quote": (a["title"] or "") , "is_synthetic": a["is_synthetic"]}
                                                    for a in advice], 3)})
    return items


def root_cause_chain(c: Corpus, supporting: list[dict], prof: dict) -> dict:
    ev = lambda kinds, labels=None: diverse_examples(
        [c.evidence(s) for a in supporting for s in c.signals_by_analysis[a["analysis_id"]]
         if s["kind"] in kinds and (labels is None or s["label"] in labels)], 2)
    top_r = [l for l, _ in prof["top_remembered"][:3]]
    top_f = [l for l, _ in prof["top_forgotten"][:3]]
    top_w = [l for l, _ in prof["top_workarounds"][:3]]
    stage = prof["dominant_failure_stage"]
    conc = prof["failure_concentration"] or 0
    # A "dominant" stage covering under 40% of breakdowns is not dominant; say so instead of implying one barrier.
    if stage and conc >= 0.4:
        barrier = f"Most breakdowns ({round(conc * 100)}%) are at one stage: {readable(stage)}, i.e. {tx.FAILURE_STAGES.get(stage, '').rstrip('.').lower()}."
        where = f"at the '{readable(stage)}' stage"
    else:
        barrier = (f"No single dominant breakdown stage: the most common, {readable(stage)}, covers only {round(conc * 100)}% of breakdowns."
                   if stage else "No breakdown stage extracted.")
        where = "at several stages"
    return {
        "symptom": {"level": "OBSERVATION", "text": f"Outcomes among supporting records: {counts_phrase(prof['outcomes'])}.", "evidence": ev(("behavior",), {"failed_retrieval", "abandoned_retrieval"})},
        "behavior": {"level": "OBSERVATION", "text": f"Most frequent workarounds: {readable_list(top_w) if top_w else 'none extracted'}.", "evidence": ev(("workaround",), set(top_w))},
        "barrier": {"level": "INSIGHT", "text": barrier, "evidence": ev(("failure",), {stage})},
        "potential_root_cause": {"level": "HYPOTHESIS",
                                 "text": f"Users retain {readable_list(top_r) if top_r else 'few extractable clues'} but lack {readable_list(top_f) if top_f else 'no specific information'}; "
                                         f"the retrieval path appears to break {where}. Validate in interviews before treating this as the cause.",
                                 "evidence": ev(("remembered", "forgotten"))},
    }


def opportunities(c: Corpus) -> list[dict]:
    by_opp: dict[str, list[dict]] = defaultdict(list)
    for a in c.relevant:
        for o in a["payload"].get("opportunity_areas") or []:
            by_opp[o].append(a)
    out = []
    for opp, supporting in by_opp.items():
        prof = profile(c, supporting, opp)
        contra = contradictions_for(c, supporting, opp)
        contradicting_records = sum(i.get("weighted_records", i["records"]) for i in contra if i["type"] in REFUTING_TYPES)
        sig_count = sum(len(c.signals_by_analysis[a["analysis_id"]]) for a in supporting)
        st = strength(prof["records"], prof["unique_sources"],
                      prof["first_person_attempts"] / prof["records"] if prof["records"] else 0,
                      contradicting_records, prof["synthetic_share"])
        unresolved = []
        blocks = Counter(a["payload"].get("forgotten_info_blocks_retrieval") for a in supporting)
        if blocks.get("unclear", 0) >= blocks.get("yes", 0):
            unresolved.append("Does the forgotten information actually cause the failure, or only co-occur with it?")
        if prof["max_single_source_share"] and prof["max_single_source_share"] > 0.5:
            unresolved.append("Is this pattern specific to one platform's user base?")
        if prof["unsuccessful"]["pct"] is not None and prof["unsuccessful"]["pct"] < 50:
            unresolved.append("Most supporting users eventually succeed; is the cost in time/effort material enough to matter?")
        unresolved += [
            "How often does this happen per user per month (frequency cannot be measured from public posts)?",
            "What did the user try that is not written in the post?",
        ]
        insights = [
            {"level": "OBSERVATION", "text": f"{prof['records']} records from {prof['unique_sources']} sources map to this area.",
             "pattern": {"source_distribution": prof["source_distribution"]}},
            {"level": "OBSERVATION", "text": f"Unsuccessful outcome in {prof['unsuccessful']['numerator']}/{prof['unsuccessful']['denominator']} supporting records; "
                                            f"abandonment signals in {prof['abandonment_signals']['numerator']}/{prof['abandonment_signals']['denominator']}.",
             "pattern": {"outcomes": prof["outcomes"]}},
            {"level": "INSIGHT", "text": f"Most-remembered clues: {', '.join(f'{readable(l)} ({n})' for l, n in prof['top_remembered'][:3]) or '—'}; "
                                        f"most-forgotten: {', '.join(f'{readable(l)} ({n})' for l, n in prof['top_forgotten'][:3]) or '—'}.",
             "pattern": {"top_remembered": prof["top_remembered"], "top_forgotten": prof["top_forgotten"]}},
            {"level": "INSIGHT", "text": f"Scenarios affected: {', '.join(f'{readable(s)} ({n})' for s, n in prof['scenarios'][:4])}.",
             "pattern": {"scenarios": prof["scenarios"]}},
        ]
        # Each insight cites the signal kinds it is actually about.
        insight_kinds = [
            (("failure",), None),
            (("behavior", "workaround"), {"failed_retrieval", "abandoned_retrieval", "abandonment", "manual_scrolling"}),
            (("remembered", "forgotten"), None),
            (("failure", "forgotten"), None),
        ]
        for ins, (kinds, labels) in zip(insights, insight_kinds):
            ins["evidence"] = diverse_examples([c.evidence(s) for a in supporting for s in c.signals_by_analysis[a["analysis_id"]]
                                                if s["kind"] in kinds and (labels is None or s["label"] in labels)], 4)
        out.append({
            "opportunity": opp,
            "description": tx.SEED_OPPORTUNITY_AREAS.get(opp, "Proposed by analyzer; PM review required."),
            "proposed": opp.startswith("proposed:"),
            "supporting_evidence_count": sig_count,
            **prof,
            "severity": {"unsuccessful": prof["unsuccessful"], "abandonment": prof["abandonment_signals"], "repeated_search": prof["repeated_search_signals"]},
            "strategic_relevance": {"vague_memory_cases": prof["vague_memory_cases"],
                                    "note": "Share of supporting records where the user both remembers and forgets something: the exact population in the business metric."},
            "evidence_strength": st,
            "contradictions": contra,
            "root_cause_chain": root_cause_chain(c, supporting, prof),
            "insights": insights,
            "unresolved_questions": unresolved,
            "record_ids": sorted({a["record_id"] for a in supporting}),
        })
    level_rank = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "DIRECTIONAL": 3}
    return sorted(out, key=lambda o: (level_rank[o["evidence_strength"]["level"]], -o["records"]))
