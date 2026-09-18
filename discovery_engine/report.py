"""Discovery bundle, discovery report (§45) and primary-research brief (§31)."""
from __future__ import annotations

from pathlib import Path

from . import taxonomy as tx
from .config import ROOT, settings
from .hypotheses import CORE_QUESTIONS, build_hypotheses, jtbd_candidates, non_leading, select_leading
from .quant import Corpus
from .store import Store, now_iso
from .decomposition import metric_decomposition
from .research import research_fit, research_fit_by_state
from .labels import counts_phrase, prettify, readable, readable_list
from .problem import METHODOLOGY, build_problem_definition
from .synthesis import opportunities, retrieval_state_profiles, segments


def build_bundle(store: Store, include_synthetic: bool = True, sources: list[str] | None = None,
                 dataset: str | None = None, save: bool = True) -> dict:
    c = Corpus(store, include_synthetic, sources, dataset)
    opps = opportunities(c)
    segs, seg_overview = segments(c)
    ret_states = retrieval_state_profiles(c)
    leading = select_leading(opps)
    chosen_opp = store.selected_target_opportunity()
    if chosen_opp and any(o["opportunity"] == chosen_opp for o in opps):
        runner = leading["leading"] if leading and leading["leading"] != chosen_opp else (leading["runner_up"] if leading else None)
        leading = {
            "leading": chosen_opp,
            "runner_up": runner,
            "rule": f"Target opportunity selected by PM: {chosen_opp}. Prioritized for primary research hypotheses and problem definition.",
            "table": leading["table"] if leading else [],
            "chosen_by_pm": True,
        }
    # A stored choice that no longer names a segment (the taxonomy changed, or the segments were rebuilt)
    # is set aside with a warning rather than carried into the plan as if it still meant something.
    chosen = store.selected_target_segment()
    stale = chosen if chosen and chosen not in {s["segment"] for s in segs} else None
    if stale:
        chosen = None
    # The research brief tests the lead and runner-up, so they must be first in line for hypotheses/JTBD
    # (the strength ordering alone can push them out of the top N).
    focus = {leading["leading"], leading["runner_up"]} if leading else set()
    prioritized = [o for o in opps if o["opportunity"] in focus] + [o for o in opps if o["opportunity"] not in focus]
    prioritized.sort(key=lambda o: 0 if leading and o["opportunity"] == leading["leading"] else 1 if o["opportunity"] in focus else 2)
    hyps = build_hypotheses(c, prioritized, top_n=len(prioritized))
    bundle = {
        "generated_at": now_iso(),
        "params": {"include_synthetic": include_synthetic, "sources": sources, "dataset": dataset},
        "scope": c.scope,
        "overview": c.overview(),
        "scenarios": c.scenarios(),
        "memory": c.memory(),
        "forgotten": c.forgotten(),
        "search": c.search_formulation(),
        "failures": c.failures(),
        "workarounds": c.workarounds(),
        "journey": c.journey(),
        "crosstab_scenario_failure": c.crosstab("retrieval_scenario", "failure_stage"),
        "crosstab_scenario_forgotten": c.scenario_x_forgotten(),
        # Behavioural retrieval segments: Direct, Contextual, Candidate-heavy, Recovery.
        "segments": segs,
        "segment_overview": seg_overview,
        # Part 3: how each segment would actually be researched, if it were chosen.
        "research_fit": research_fit(c, segs),
        "retrieval_states": ret_states,
        "research_fit_by_state": research_fit_by_state(c, ret_states),
        "opportunities": opps,
        "leading": leading,
        "hypotheses": hyps,
        "jtbd": jtbd_candidates(c, prioritized),
        # Part 2: the business metric broken into stage outcomes, each sized from the evidence.
        "decomposition": metric_decomposition(c),
        "target_segment": chosen,
        "target_segment_stale": stale,
        "target_opportunity": chosen_opp,
    }
    syn = c.scope["synthetic_records"]
    bundle["provenance"] = {
        "mode": settings.provenance,
        "datasets": sorted({r["dataset"] for r in c.records}),
        "flagged_records": syn,
        # In "neutral" mode outputs name the dataset and make no claim about where the text came from;
        # the per-record flag and the provenance note in problemstatement.md §22.5 are unchanged.
        "note": (f"{syn} of {len(c.records)} records are flagged as generated. Patterns reflect that data, not real users."
                 if syn and settings.provenance == "auto" else None),
    }
    bundle["_record_scenarios"] = {a["record_id"]: a["payload"].get("retrieval_scenario") for a in c.relevant}
    bundle["research_brief"] = research_brief(bundle)
    # Part 4: problem definition assembled from the same evidence, DRAFT until interviews run.
    bundle["problem_definition"] = build_problem_definition(bundle, c, bundle["target_segment"])
    del bundle["_record_scenarios"]
    if save:
        store.save_synthesis("discovery", bundle, bundle["params"])
    return bundle


def recruitment_mix(b: dict, interviews: int = 6, coverage_goal: float = 0.6) -> dict:
    """Which behavioural segments to recruit from, so the interviews cover the attempts behind BOTH tested opportunities.

    A single "target segment" misleads when evidence is spread out, so segments are added in order of
    coverage until they reach the goal, and interview slots are split in proportion.
    """
    tested = [b["leading"]["leading"], b["leading"]["runner_up"]]
    records = set()
    for o in b["opportunities"]:
        if o["opportunity"] in tested:
            records |= set(o["record_ids"])
    seg_of = {rid: s["segment"] for s in b["segments"] for rid in s["record_ids"] if rid in records}
    total = len(seg_of) or 1
    groups = [(s["segment"], sum(1 for v in seg_of.values() if v == s["segment"])) for s in b["segments"]]
    groups.sort(key=lambda g: -g[1])
    chosen, covered = [], 0
    for name, n in groups:
        if n == 0 or (covered / total >= coverage_goal and len(chosen) >= 2) or len(chosen) >= 3:
            break
        chosen.append((name, n))
        covered += n
    slots = [max(1, round(interviews * n / max(1, covered))) for _, n in chosen]
    while sum(slots) > interviews:
        slots[slots.index(max(slots))] -= 1
    while sum(slots) < interviews:
        slots[0] += 1
    return {
        "records_behind_tested_opportunities": len(seg_of),
        "coverage": {"numerator": covered, "denominator": len(seg_of), "pct": round(100 * covered / total, 1),
                     "denominator_definition": "retrieval attempts behind the two tested opportunities",
                     "directional": len(seg_of) < 30},
        "segments": [{"segment": name, "records": n, "interviews": s} for (name, n), s in zip(chosen, slots)],
        # Effortless finds are rare in public posts, so they rarely win seats on coverage alone.
        "contrast_note": ("Consider swapping one seat for a Direct Retrieval participant as a contrast case: "
                          "they show what a strong identifier looks like when it works."),
    }


def research_brief(b: dict) -> dict:
    if not b["leading"]:
        return {}
    lead = next(o for o in b["opportunities"] if o["opportunity"] == b["leading"]["leading"])
    top_hyps = [h for h in b["hypotheses"] if h["opportunity"] in (b["leading"]["leading"], b["leading"]["runner_up"])]
    mix = recruitment_mix(b)
    cov = mix["coverage"]
    chosen = b.get("target_segment")
    # When the PM has chosen a segment, the screener and session adapt to it; otherwise the generic ones stand.
    fit = (b.get("research_fit") or {}).get(chosen or "", {})
    return {
        "status": "PLAN ONLY. No interview findings exist yet. Do not fill this section with assumed results.",
        "target_segment": chosen or (" + ".join(s["segment"] for s in mix["segments"]) or None),
        "target_segment_chosen_by_pm": bool(chosen),
        "methodology": {**METHODOLOGY, "segment_adaptation": fit.get("session_shape"),
                        "segment_recruitability": fit.get("recruitability"), "segment_sensitivity": fit.get("sensitivity"),
                        "segment_observability": fit.get("observability"), "adapted_for": chosen},
        "target_segment_rationale": ((f"Selected by the PM. Suggested mix if you want full coverage: " if chosen else "")
                                     + f"Together these cover {cov['numerator']} of {cov['denominator']} records ({cov['pct']}%) behind the two tested opportunities. "
                                     f"Suggested mix of {sum(s['interviews'] for s in mix['segments'])} interviews: "
                                     + "; ".join(f"{s['interviews']} × {s['segment']} ({s['records']} records)" for s in mix["segments"]) + "."),
        "recruitment_mix": mix,
        "retrieval_scenarios": [s for s, _ in lead["scenarios"][:3]],
        "top_opportunity_areas": [b["leading"]["leading"], b["leading"]["runner_up"]],
        "hypotheses": top_hyps,
        "contradictory_evidence": lead["contradictions"],
        "unknowns": lead["unresolved_questions"],
        "interview_objectives": [
            "Reconstruct 1-2 recent, real retrieval episodes per participant, step by step.",
            "Identify what was remembered and what was missing at the start of each episode.",
            "Locate the stage where the episode broke down (recall / express / match / recognize / recover, or the data layer).",
            "Observe workarounds and the point of abandonment.",
            "Test each hypothesis against its falsification signals.",
        ],
        "screener": fit.get("screener") or [
            "In the last 3 months, have you tried to find a specific old photo, video, screenshot or document on your phone that you could not find right away? (must be yes)",
            "What was it? (capture the scenario; recruit toward the target scenarios)",
            "Roughly how many photos are in your library? (capture only, do not exclude)",
            "Have you worked in photography, search or machine learning? (exclude: they narrate the system, not the memory)",
        ],
        "screener_is_segment_specific": bool(fit.get("screener")),
        "interview_questions": non_leading(CORE_QUESTIONS + [q for h in top_hyps for q in h["interview_questions"]]),
        "behaviors_to_observe": [e for h in top_hyps for e in h["we_expect_to_observe"]],
        "signals_to_validate": [x for h in top_hyps for x in h["because"]],
        "falsification_signals": [x for h in top_hyps for x in h["falsification_signals"]],
        "method_notes": [
            "Elicit the memory before the device is in hand. The gap between what they remember and what they type is the finding.",
            "Let them attempt it unaided first. Help only in the final assisted-resolution step, never before.",
            "Avoid naming any solution. Do not ask whether they would use a feature.",
            "Record the exact queries typed, and note what they remembered but did not type.",
            "End every episode knowing whether the item existed and was indexed. Without that, a failure cannot be attributed.",
        ],
    }


# ---------------------------------------------------------------------------
def _r(x: dict | None) -> str:
    if not x:
        return "—"
    pct = f" ({x['pct']}%)" if x.get("pct") is not None else ""
    return f"{x['numerator']}/{x['denominator']}{pct}{' †' if x.get('directional') else ''}"


def _ev(items: list[dict], k: int = 3) -> str:
    lines = []
    for e in items[:k]:
        tag = " [SYNTHETIC]" if e.get("is_synthetic") and settings.provenance == "auto" else ""
        lines.append(f"  - `{e.get('evidence_id') or e['record_id']}` ({e['source']}{tag}): “{(e.get('quote') or '').strip()[:220]}”")
    return "\n".join(lines) or "  - (no validated evidence)"


def _table(rows: list[dict], cols: list[tuple[str, str]]) -> str:
    head = "| " + " | ".join(h for h, _ in cols) + " |\n|" + "---|" * len(cols)
    body = "\n".join("| " + " | ".join(str(fn(r)) for _, fn in cols) + " |" for r in rows)
    return f"{head}\n{body}"


def render_report(b: dict) -> str:
    o = b["overview"]
    prov = b.get("provenance", {})
    out = [f"# Discovery Report: Retrieving Vaguely Remembered Photos\n\nGenerated {b['generated_at']}."]
    out.append(f"> **Dataset:** `{', '.join(prov.get('datasets') or ['—'])}` · {o['total_records']} records, {o['unique_records']} unique.")
    out.append("> **Dashboard:** [http://127.0.0.1:8000](http://127.0.0.1:8000) (`python -m discovery_engine serve`)")
    if prov.get("note"):
        out.append(f"> **⚠ SYNTHETIC / SIMULATED DATA.** {prov['note']}")
    out.append("† = denominator below the minimum sample; treat as directional. Every rate is numerator/denominator of distinct records.\n")

    out.append("## 1. Business Metric\nIncrease the percentage of users who successfully retrieve a photo they remember but cannot precisely describe when they start searching.")
    d = b["decomposition"]
    stage_names = {"recall": "Recall", "express": "Express", "match": "Match", "recognize": "Recognize",
                   "recover": "Recover", "data": "Data & index", "other": "Other"}
    out.append("## 2. Product Outcome Decomposition\n"
               f"Baseline: **{_r(d['baseline'])} attempts end in a confirmed find**; {_r(d['unresolved'])} do not.\n\n"
               + "Five things have to go right for a vaguely remembered photo to be found:\n\n"
               + "\n".join(f"{i + 1}. **{stage_names[x['stage']]}** — {x['condition']}"
                           for i, x in enumerate(x for x in d["stages"] if x["in_journey"]))
               + "\n\nPlus one condition outside the user's journey: "
               + next((x["condition"] for x in d["stages"] if x["stage"] == "data"), "") + "\n\n"
               + _table([x for x in d["stages"] if x["in_journey"] or x["breaks_here"]["numerator"]], [
                   ("Stage", lambda r: stage_names.get(r["stage"], r["stage"]) + ("" if r["in_journey"] else " (outside the journey)")),
                   ("Product outcome to influence", lambda r: r["product_outcome"]),
                   ("Breaks here", lambda r: _r(r["breaks_here"])),
                   ("Still unresolved", lambda r: _r(r["unresolved_here"])),
                   ("Max headroom (pts)", lambda r: f"+{r['max_headroom_pts']}"),
                   ("Opportunity areas", lambda r: ", ".join(f"{readable(o)} ({n})" for o, n in r["opportunities"]) or "—"),
               ])
               + f"\n\n*{d['headroom_note']}*"
               + f"\n\nRanked by recoverable share: {readable_list(d['ranked_by_headroom'])}. "
               + f"{_r(d['no_breakdown_described'])} of attempts describe no breakdown; {_r(d['breakdown_unclear'])} are unclear.")
    out.append("\n".join([
        "## 3. Discovery Scope",
        f"- Scope: {b['scope']['label']}",
        f"- Sources: {b['scope']['sources']}",
        f"- Analyzers: {b['scope']['analyzers']}",
        f"- Duplicates excluded: {o['duplicates_excluded']}",
        f"- Relevant to retrieval: {_r(o['relevant'])}; first-person retrieval attempts among relevant: {_r(o['retrieval_attempts'])}",
        f"- Quote validation: {o['quote_validation']['quotes_invalid']} of {o['quote_validation']['quotes_total']} extracted quotes could not be found in the source and were excluded.",
        "- Method: staged extraction (relevance, then structured signals with verbatim quotes), deterministic validation, record-level counting, rule-based evidence strength, counter-evidence search.",
    ]))

    out.append("## 4. User Retrieval Scenarios\n" + _table(b["scenarios"][:18], [
        ("Scenario", lambda r: readable(r["label"])), ("Attempts", _r), ("Sources", lambda r: r["source_count"]),
        ("Unsuccessful", lambda r: sum(v["numerator"] for k, v in r["outcomes"].items() if k in ("not_found", "abandoned", "partially_found", "uncertain"))),
        ("Top failure stage", lambda r: readable(next((k for k in r["failure_stages"] if k not in ("none_observed", "unclear")), None))),
        ("Top forgotten", lambda r: readable_list(l for l, _ in r["top_forgotten"][:2])),
    ]))

    out.append("## 5. Memory Patterns (what people remember)\n" + _table(b["memory"], [
        ("Remembered", lambda r: readable(r["label"])), ("Attempts", _r), ("Sources", lambda r: r["source_count"]),
        ("Precision (exact/approx)", lambda r: f"{r['precision'].get('exact', 0)}/{r['precision'].get('approximate', 0)}"),
    ]))
    for r in b["memory"][:3]:
        out.append(f"- **{readable(r['label'])}** examples:\n{_ev(r['examples'])}")

    out.append("## 6. Forgotten Information\n" + _table(b["forgotten"], [
        ("Forgotten", lambda r: readable(r["label"])), ("Attempts", _r),
        ("Unsuccessful when forgotten", lambda r: _r(r["unsuccessful_when_forgotten"])),
        ("Unsuccessful when not", lambda r: _r(r["unsuccessful_when_not_forgotten"])),
        ("Text links gap to failure", lambda r: _r(r["explicitly_blocks_retrieval"])),
    ]) + "\n\n*These are associations, not causes. 'Text links gap to failure' counts only records where the author connects the two.*")

    s = b["search"]
    out.append("\n".join([
        "## 7. Search Formulation",
        f"- Attempts quoting at least one query: {_r(s['attempts_with_quoted_query'])}; median query length: {s['median_query_words']} words",
        f"- Attempts with 2+ queries: {_r(s['multiple_attempts'])}",
        "- Query types: " + ", ".join(f"{readable(k)} {_r(v)}" for k, v in s["query_types"].items()),
        "- Query orientation: " + ", ".join(f"{readable(k)} {_r(v)}" for k, v in s["orientation"].items()),
        "- Outcome by query type: " + "; ".join(f"{readable(k)}: {counts_phrase(v)}" for k, v in s["outcome_by_query_type"].items()),
        "- Example queries:\n" + _ev(s["examples"], 6),
    ]))

    out.append("## 8. Failure Patterns\n" + _table(b["failures"], [
        ("Stage", lambda r: readable(r["label"])), ("Attempts", _r), ("Sources", lambda r: r["source_count"]), ("Meaning", lambda r: r["description"]),
    ]))
    for r in b["failures"][:4]:
        if r["examples"]:
            out.append(f"- **{readable(r['label'])}**:\n{_ev(r['examples'], 2)}")
    out.append("\n**Journey (difficulty by stage):** " + " → ".join(
        f"{j['stage']} {_r(j['records_with_difficulty'])}" for j in b["journey"]))

    out.append("## 9. Workarounds\n" + _table(b["workarounds"], [
        ("Workaround", lambda r: readable(r["label"])), ("Attempts", _r), ("Sources", lambda r: r["source_count"]),
    ]))

    so = b["segment_overview"]
    im = so["impact_map"]
    out.append("## 10. Retrieval Segments (by user behaviour)\n"
               + "**Primary segmentation is binary.** Person, place, event, object and visual detail are memory clues "
               "used to characterize attempts, not separate segments; candidate-heavy and recovery-dependent outcomes "
               "are retrieval states within these segments (below), not segments of their own.\n\n"
               + "\n".join(f"{s['number']}. **{s['segment']}** — {s['definition']}" for s in b["segments"])
               + "\n\n" + _table(b["segments"], [
                   ("Segment", lambda r: r["segment"]), ("Share of attempts", lambda r: _r(r["share_of_attempts"])),
                   ("Sources", lambda r: r["unique_sources"]), ("Found", lambda r: _r(r["found"])),
                   ("Unsuccessful", lambda r: _r(r["unsuccessful"])), ("Abandon", lambda r: _r(r["abandonment_signals"])),
                   ("Dominant breakdown", lambda r: readable(r["dominant_failure_stage"])),
                   ("Strength", lambda r: r["evidence_strength"]["level"]),
               ])
               + "\n\n**How attempts are placed.** " + so["rules"]["precedence"]
               + f"\n\n*{so['note_on_direct']}*"
               + "\n\n### Impact mapping\n"
               + f"**WHY** {im['why']}\n\n**WHO** {im['who']}\n\n**HOW** {im['how']}\n\n**WHAT** {im['what_note']}"
               + f"\n\n**Target segment hypothesis (to validate, not a conclusion):** {so['target_segment_hypothesis']}")
    _seg_name = {"direct": "Direct", "contextual": "Contextual"}
    out.append("### Retrieval states\nHow attempts within the segments above actually played out. Not exclusive user "
               "groups: every attempt gets exactly one state, by the precedence rule below (data/index limitation, "
               "then a crowded result set, then a changed route after a failed first try, then a clean find, else "
               "unresolved).\n\n"
               + _table(b["retrieval_states"], [
                   ("State", lambda r: r["state"]), ("Definition", lambda r: r["definition"]),
                   ("Share of attempts", lambda r: _r(r["share_of_attempts"])),
                   ("Sources", lambda r: r["unique_sources"]),
                   ("Mostly in", lambda r: ", ".join(f"{_seg_name.get(k, k)} ({n})" for k, n in r["primary_mix"])),
                   ("Strength", lambda r: r["evidence_strength"]["level"]),
               ]))
    lens_md = ["### Secondary segmentation\nThe Direct/Contextual split is the primary cut; each lens below cuts across it."]
    for key, L in so["secondary"].items():
        cols = [("Category", lambda r: r["label"]), ("Share of attempts", lambda r: _r(r["rate"]))]
        if key != "retrieval_state":
            cols += [("Found (of attempts stating an outcome)", lambda r: _r(r["found"])),
                     ("Photo not there to find", lambda r: _r(r["data_missing"]))]
        mix = "; ".join(
            f"{s['segment']}: " + ", ".join(f"{c['label']} {L['by_segment'][s['key']][c['key']]['pct']}%"
                                            for c in L["categories"] if L["by_segment"][s["key"]][c["key"]]["numerator"])
            for s in b["segments"])
        lens_md.append(f"#### {L['name']}\n*{L['question']}* {L['rule']}\n\n" + _table(L["categories"], cols)
                       + f"\n\nWithin each segment: {mix}.")
    lens_md.append("*Read the find rates as composition, not cause: posts that failed are longer and list more of what "
                   "the person remembers, so part of any gradient is how people write. The interview memory card measures it properly.*")
    out.append("\n\n".join(lens_md))

    out.append("## 11. Opportunity Areas")
    for op in b["opportunities"]:
        out.append(f"### {readable(op['opportunity'])} ({op['evidence_strength']['level']})\n`{op['opportunity']}` · {op['description']}\n")
        for ins in op["insights"]:
            out.append(f"- **{ins['level']}**: {prettify(ins['text'])}")
        rc = op["root_cause_chain"]
        out.append("- **Evidence chain:** " + " → ".join(f"*{readable(k)}* ({v['level']}): {prettify(v['text'])}" for k, v in rc.items()))
        out.append("- Evidence:\n" + _ev(op["insights"][0]["evidence"], 3))
        if op["contradictions"]:
            out.append("- **Challenging evidence:**\n" + "\n".join(f"  - {readable(x['type'])} ({x['records']} records): {prettify(x['description'])}" for x in op["contradictions"]))
        out.append("- **Unresolved:** " + " / ".join(op["unresolved_questions"]))

    out.append("## 12. Opportunity Comparison\n" + _table(b["opportunities"], [
        ("Opportunity", lambda r: readable(r["opportunity"])), ("Records", lambda r: r["records"]), ("Signals", lambda r: r["supporting_evidence_count"]),
        ("Sources", lambda r: r["unique_sources"]), ("Vague-memory cases", lambda r: _r(r["vague_memory_cases"])),
        ("Unsuccessful", lambda r: _r(r["unsuccessful"])), ("Abandon", lambda r: _r(r["abandonment_signals"])),
        ("Refuting records", lambda r: sum(x["records"] for x in r["contradictions"] if x["type"] == "explicit_counter_evidence")),
        ("Vague-memory successes", lambda r: sum(x["records"] for x in r["contradictions"] if x["type"] == "vague_memory_success")),
        ("Strength", lambda r: r["evidence_strength"]["level"]),
    ]) + "\n\nEvidence-strength rules: " + "; ".join(f"{k}: {v}" for k, v in (b["opportunities"][0]["evidence_strength"]["rules"].items() if b["opportunities"] else [])))

    lead = b["leading"]
    if lead:
        out.append("## 13. Leading Opportunity (proposal for PM review)\n"
                   f"**{readable(lead['leading'])}**, runner-up **{readable(lead['runner_up'])}**.\n\nSelection rule: {lead['rule']}\n\n"
                   + _table(lead["table"], [("Opportunity", lambda r: readable(r["opportunity"])), ("Strength", lambda r: r["strength"]), ("Vague-memory %", lambda r: r["vague_memory_pct"]), ("Unsuccessful %", lambda r: r["unsuccessful_pct"]), ("Sources", lambda r: r["sources"]), ("Records", lambda r: r["records"])]))
    out.append("## 14. Research Hypotheses")
    for h in b["hypotheses"]:
        out.append(f"### {readable(h['opportunity'])} (evidence: {h['evidence_strength']})\n**{h['we_believe']}**\n\n**BECAUSE**\n"
                   + "\n".join(f"- {x}" for x in h["because"])
                   + "\n\n**WE EXPECT TO OBSERVE**\n" + "\n".join(f"- {x}" for x in h["we_expect_to_observe"])
                   + "\n\n**WE NEED TO VALIDATE**\n" + "\n".join(f"- {x}" for x in h["we_need_to_validate"])
                   + "\n\n**WOULD FALSIFY**\n" + "\n".join(f"- {x}" for x in h["falsification_signals"])
                   + "\n\nEvidence:\n" + _ev(h["evidence"], 3))
    pd = b.get("problem_definition") or {}
    if pd.get("status"):
        out.append("## 15. Problem Definition (draft)\n> " + pd["status"])
        for key, label in [("target_user_segment", "Target user segment"), ("retrieval_scenario", "Retrieval scenario"),
                           ("product_outcome", "Product outcome to influence"), ("root_cause", "Root cause of retrieval failure"),
                           ("existing_workarounds", "Existing user workarounds"), ("user_value", "Why solving it creates user value"),
                           ("business_rationale", "Why it makes business sense"), ("not_this_problem", "What this problem is not"),
                           ("competing_explanation", "Competing explanation to rule out")]:
            f = pd.get(key)
            if not f:
                continue
            block = [f"### {label} ({f['level']})", f["text"]]
            if f.get("evidence_basis"):
                block.append(f"*{f['evidence_basis']}*")
            if f.get("confirm_in_research"):
                block.append(f"**To settle in interviews:** {f['confirm_in_research']}")
            if f.get("open_questions"):
                block.append("**Open, not answerable from public posts:**\n" + "\n".join(f"- {q}" for q in f["open_questions"]))
            if f.get("evidence"):
                block.append(_ev(f["evidence"], 2))
            out.append("\n\n".join(block))
        out.append("### How the thinking evolved\n" + "\n".join(
            f"{i + 1}. **{e['step']}** ({e['level']}): {e['text']}" for i, e in enumerate(pd["evolution"])))
    out.append("## JTBD candidates (INTERPRETATION)")
    for j in b["jtbd"]:
        out.append(f"- *{readable(j['opportunity'])}*: {j['jtbd']} (stated goals in {j['records_with_stated_goal']}/{j['supporting_records']} records)\n{_ev(j['goal_evidence'], 2)}")
    return "\n\n".join(out) + "\n"


def _methodology_md(m: dict | None) -> str:
    if not m:
        return ""
    adapt = m.get("segment_adaptation") or {}
    return "\n\n".join([x for x in [
        f"## Methodology\n**{m['method']}**" + (f"\n\n*{m['one_line']}*" if m.get("one_line") else ""),
        "**Why this method**\n" + "\n".join(f"- {x}" for x in m["why"]),
        ("**What each part of the session buys**\n" + "\n".join(
            f"- *{d['element']}* — {d['what']} **Buys:** {d['buys']}" for d in m["design"])) if m.get("design") else "",
        f"**Participants**\n{m['participants']}",
        (f"**Adapted for the chosen segment ({m['adapted_for']})**\n"
         + "\n".join(f"- {x}" for x in adapt.get("changes", []))) if adapt.get("changes") else "",
        "**Session plan**\n" + "\n".join(f"{i + 1}. {x}" for i, x in enumerate(m["session"])),
        "**Capture in every episode**\n" + "\n".join(f"- {x}" for x in m["instrumentation"]),
        "**Analysis plan**\n" + "\n".join(f"- {x}" for x in m["analysis"]),
        "**Alternatives considered**\n" + "\n".join(f"- {a['method']}: {a['rejected_because']}" for a in m["alternatives_considered"]),
        "**Ethics and privacy**\n" + "\n".join(f"- {x}" for x in m["ethics_and_privacy"]),
        "**Threats to validity**\n" + "\n".join(f"- {x}" for x in m["validity_threats"]),
    ] if x])


def render_brief(b: dict) -> str:
    rb = b.get("research_brief") or {}
    if not rb:
        return "# Research Brief\n\nNo opportunities available yet.\n"
    prov = b.get("provenance", {})
    lines = ["# Primary Research Brief (5–6 interviews)", f"Generated {b['generated_at']}. **{rb['status']}**",
             f"Dataset: `{', '.join(prov.get('datasets') or ['—'])}`."]
    if prov.get("note"):
        lines.append(f"> **⚠ Built from SYNTHETIC / SIMULATED data.** {prov['note']} Rebuild from real evidence before recruiting.")
    lines += [
        f"## Target segment\n{rb['target_segment']}. {rb['target_segment_rationale']}",
        "## Retrieval scenarios\n" + readable_list(rb["retrieval_scenarios"]),
        "## Opportunity areas under test\n" + "\n".join(f"- **{readable(x)}** (`{x}`): {tx.SEED_OPPORTUNITY_AREAS.get(x, '')}" for x in rb["top_opportunity_areas"] if x),
        "## Hypotheses\n" + "\n".join(f"- {h['we_believe']}" for h in rb["hypotheses"]),
        "## Evidence behind each hypothesis\n" + "\n".join(f"- *{readable(h['opportunity'])}*: " + " ".join(h["because"]) + "\n" + _ev(h["evidence"], 2) for h in rb["hypotheses"]),
        "## Contradictory evidence\n" + "\n".join(f"- {readable(x['type'])} ({x['records']}): {prettify(x['description'])}" for x in rb["contradictory_evidence"]),
        "## Unknowns\n" + "\n".join(f"- {x}" for x in rb["unknowns"]),
        "## Interview objectives\n" + "\n".join(f"- {x}" for x in rb["interview_objectives"]),
        "## Screener\n" + "\n".join(f"- {x}" for x in rb["screener"]),
        "## Interview questions (behavioural, non-leading)\n" + "\n".join(f"{i}. {q}" for i, q in enumerate(rb["interview_questions"], 1)),
        "## Behaviours to observe\n" + "\n".join(f"- {x}" for x in rb["behaviors_to_observe"]),
        "## Signals to validate\n" + "\n".join(f"- {x}" for x in rb["signals_to_validate"]),
        "## Signals that would falsify the hypotheses\n" + "\n".join(f"- {x}" for x in rb["falsification_signals"]),
        "## Method notes\n" + "\n".join(f"- {x}" for x in rb["method_notes"]),
        _methodology_md(rb.get("methodology")),
        "## Findings\n_Not yet collected._",
    ]
    return "\n\n".join(lines) + "\n"


def write_reports(b: dict, out_dir: Path | None = None) -> tuple[Path, Path]:
    out_dir = out_dir or ROOT / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    rp, bp = out_dir / "discovery_report.md", out_dir / "research_brief.md"
    rp.write_text(render_report(b), encoding="utf-8")
    bp.write_text(render_brief(b), encoding="utf-8")
    return rp, bp
