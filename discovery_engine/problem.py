"""Research methodology (Part 3) and the problem-definition draft (Part 4).

Everything here is assembled from stored evidence and clearly staged:
  * OBSERVATION  - counted from the corpus
  * INTERPRETATION - the PM's reading of those counts
  * HYPOTHESIS   - to be confirmed or killed in interviews
  * OPEN         - cannot be answered from public posts at all

The problem definition is a DRAFT until interviews are done. Fields that interviews
must settle carry `confirm_in_research`, and no field is ever filled with an
assumed finding.
"""
from __future__ import annotations

from collections import Counter

from .decomposition import STAGE_OF_FAILURE, stage_summary
from .labels import readable, readable_list
from .quant import Corpus, diverse_examples

METHODOLOGY = {
    "method": ("Hybrid retrieval-episode study on the participant's own library: memory elicitation first, then an "
               "unaided live attempt, then a walkthrough of a past failure, then assisted resolution"),
    "one_line": ("Capture what the person remembers before they touch the app, watch them search with exactly that, "
                 "then find out whether the photo was ever findable."),
    "why": [
        "The corpus is already retrospective self-report. More interviews of the same kind would add volume, not a new "
        "kind of evidence. The session has to produce something public posts cannot: observed behaviour, and ground truth.",
        "The problem is a gap between the memory a person holds and the query the system needs. That gap is only "
        "measurable if the memory is captured *before* the search, so the elicitation comes first and is never skipped.",
        "Asking someone to recall how they tried to recall is doubly unreliable. A live attempt removes one layer of recall "
        "bias; the walkthrough is kept for episodes that cannot be reproduced, not as the main instrument.",
        "22.3% of attempts in the corpus break down because the item or its metadata is missing. Nothing in an interview "
        "separates 'could not find it' from 'it was never there' unless the session ends by finding the item together.",
        "Discovery, not validation: no prototype exists yet, so nothing is shown to react to.",
    ],
    "design": [
        {"element": "Memory elicitation before search",
         "what": "For each target, the participant fills a spoken memory card: time, people, place, objects, text, "
                 "appearance, occasion, and how sure they are of each. No device in hand yet.",
         "buys": "The held memory, independent of the query. The difference between this card and what they later type "
                 "is the express-stage gap, which the engine can never see in a public post."},
        {"element": "Seeded, unaided live attempt",
         "what": "The participant nominates 2-3 photos at recruitment that they know exist but could not find. They "
                 "attempt one now, unaided, thinking aloud. Success is their own recognition, not a known file.",
         "buys": "Observed express, match, recognize and recover behaviour, in their real library, at real scale."},
        {"element": "Retrospective walkthrough",
         "what": "One past episode reconstructed step by step: what they needed and why, what they searched, what came "
                 "back, what they tried next, how it ended.",
         "buys": "Episodes that cannot be reproduced to order, above all the ones they abandoned."},
        {"element": "Assisted resolution, last",
         "what": "The moderator helps find the item, by any means, and records whether it existed, whether it was "
                 "indexed, and what finally worked.",
         "buys": "Ground truth per episode: user-stage failure or data/index limitation. Kept last so nothing teaches "
                 "the participant mid-session."},
    ],
    "alternatives_considered": [
        {"method": "Retrospective interview only (no live task)",
         "rejected_because": "This was the earlier plan. It repeats the evidence type the corpus already has, and asks "
                             "people to recall a memory failure from memory. Kept as one part of the session, not the whole."},
        {"method": "Lab task with a researcher-supplied library",
         "rejected_because": "Perfectly controlled and entirely beside the point: the participant's own memory of their "
                             "own photos is the thing under study, and it cannot be transplanted."},
        {"method": "Survey at scale",
         "rejected_because": "Self-reported frequency would not show where the attempt breaks down, and the engine already gives breadth."},
        {"method": "Diary study over 2-4 weeks",
         "rejected_because": "Best for frequency, which public posts cannot answer, but too slow for this decision. Worth running after the problem is defined."},
        {"method": "Usability test of a concept",
         "rejected_because": "Premature: it tests a solution before the problem is defined, and invites solution bias."},
        {"method": "Log analysis of search sessions",
         "rejected_because": "Would answer frequency and drop-off precisely, but requires product telemetry this study has no access to."},
    ],
    "participants": ("5-6 participants from the target segment, recruited against that segment's screener, mixed across "
                     "the retrieval scenarios that carry the evidence. Purposive, not representative: this study "
                     "establishes mechanism, and the corpus rates stay the estimate of prevalence."),
    "session": [
        "5 min: consent, what will and will not be recorded, how the session works (no right answers, no product shown).",
        "10 min: library context - size, age, devices, sharing, and how they usually find things.",
        "10 min: memory elicitation for the nominated targets, device face-down. What do they remember, and how sure are they of each clue?",
        "15 min: unaided live attempt on their own library, thinking aloud. The moderator does not help, name features or suggest terms.",
        "12 min: walkthrough of one past episode that cannot be reproduced, especially one they gave up on.",
        "5 min: assisted resolution - find it together, and record whether it was there, indexed, and what worked.",
        "3 min: close - anything they expected to be asked, and what they would have done next if the session had not happened.",
    ],
    "instrumentation": [
        "The memory card per target: each clue, and the participant's own confidence in it, before any searching.",
        "Every query verbatim, in order, with its timestamp, and whether it was typed, spoken or browsed.",
        "The clue delta: which remembered clues reached the query, which were dropped, and which were reworded.",
        "The stage where each episode broke down, in the engine's own model (recall, express, match, recognize, recover, or the data layer).",
        "Recognition behaviour: how far they scrolled, how long they looked, whether they passed over the target and came back.",
        "Workarounds in order, and the exact point at which they stopped.",
        "Resolution: found or not, by what means, and whether the item turned out to be missing, unindexed or simply unreachable by search.",
    ],
    "analysis": [
        "Code each episode into the journey stages and the memory/forgotten label sets, using the engine's taxonomy so interviews and corpus can be compared directly.",
        "Tabulate the clue delta across participants: held vs expressed vs what the system needed. This is the primary analysis, not a side observation.",
        "Classify every episode's resolution as user-stage failure or data/index limitation before interpreting anything else.",
        "Two people code the first two transcripts independently and reconcile before the rest.",
        "Compare each hypothesis against its falsification signals before looking for support.",
        "Log every disconfirming episode explicitly; a single well-evidenced counter-case is enough to reopen the leading opportunity.",
        "Stop-rule check: if the last two sessions produce no new stage, clue or workaround, treat coverage as sufficient for this decision.",
    ],
    "ethics_and_privacy": [
        "Screen share is opt-in, per episode, and off by default for segments whose material is sensitive. The participant always drives their own device.",
        "Do not capture, store or ask for photo content. Record queries, outcomes and behaviour, never images.",
        "Nominated targets are described by the participant in their own words at recruitment; they are never asked to send a photo.",
        "No names, faces or locations in notes; refer to participants by code.",
        "Say plainly that this is research, that no product is being sold, and that they can stop or skip any episode at any time.",
    ],
    "validity_threats": [
        "Recall bias: participants narrate a tidier attempt than happened. Mitigation: the live attempt is the primary instrument, and the walkthrough asks for the last time, not the typical time.",
        "Seeding artificiality: a nominated target is not a spontaneous need, so urgency and give-up behaviour may differ. Mitigation: pair every seeded attempt with one unseeded past episode, and compare.",
        "Moderator contamination: helping, or naming a stage or feature, teaches the participant mid-session. Mitigation: assisted resolution is last, and the guide is solution-free and filtered for leading questions.",
        "Selection bias: the screener recruits people who remember failing, over-representing failure. Mitigation: also ask for the most recent successful retrieval in each session.",
        "Corpus bias carried into recruitment: the engine's evidence is public complaint-shaped text. Mitigation: recruit across scenarios, not only the ones with the most posts.",
        "Small n: 5-6 sessions establish mechanism, not rates. Mitigation: never report interview percentages; carry prevalence questions to telemetry or a diary study.",
    ],
}


def _ev(c: Corpus, records: set[str], kinds: tuple[str, ...], labels: set[str] | None = None, k: int = 3) -> list[dict]:
    pool = [c.evidence(s) for a in c.relevant if a["record_id"] in records
            for s in c.signals_by_analysis[a["analysis_id"]]
            if s["kind"] in kinds and (labels is None or s["label"] in labels)]
    return diverse_examples(pool, k)


def build_problem_definition(b: dict, c: Corpus, target_segment: str | None = None) -> dict:
    """Assemble the Part 4 problem definition from the current evidence. Draft until interviews run."""
    if not b.get("leading"):
        return {}
    lead = next(o for o in b["opportunities"] if o["opportunity"] == b["leading"]["leading"])
    runner = next((o for o in b["opportunities"] if o["opportunity"] == b["leading"]["runner_up"]), None)
    dec = b["decomposition"]
    ids = set(lead["record_ids"])
    rb = b.get("research_brief") or {}
    segment = target_segment or rb.get("target_segment")

    # Which stage does the leading opportunity's evidence break at, and what outcome does that imply?
    stage_counts = Counter(STAGE_OF_FAILURE.get(a["payload"].get("failure_stage"))
                           for a in c.relevant if a["record_id"] in ids)
    stage_counts.pop(None, None)
    stage = stage_counts.most_common(1)[0][0] if stage_counts else None
    stage_row = stage_summary(dec, stage) if stage else None

    scenarios = lead["scenarios"][:3]
    goals = [a for a in c.relevant if a["record_id"] in ids and a["payload"].get("user_goal")]
    goal_ev = diverse_examples([{**c.evidence({"record_id": a["record_id"], "source": a["source"], "platform": a["platform"],
                                               "source_url": a["source_url"], "source_date": a["source_date"],
                                               "kind": "user_goal", "label": "user_goal", "value": "",
                                               "quote": a["payload"]["user_goal"], "is_synthetic": a["is_synthetic"],
                                               "evidence_id": None})} for a in goals], 3)
    abandoned = lead["abandonment_signals"]
    work = lead["top_workarounds"][:4]

    return {
        "status": "DRAFT — built from discovery evidence only. Interviews (Part 3) confirm, refine or kill each field.",
        "target_user_segment": {
            "level": "INTERPRETATION",
            "text": segment or "Not selected yet",
            "evidence_basis": rb.get("target_segment_rationale", ""),
            "confirm_in_research": "Do participants recruited this way actually recognise the episode we think they have?",
        },
        "retrieval_scenario": {
            "level": "OBSERVATION",
            "text": (f"Retrieving {readable_list([s for s, _ in scenarios])} items from a personal library, months or years later, "
                     f"while still remembering {readable_list([l for l, _ in lead['top_remembered'][:3]])} "
                     f"and no longer holding {readable_list([l for l, _ in lead['top_forgotten'][:2]])}."),
            "counts": scenarios,
            "evidence": _ev(c, ids, ("remembered", "forgotten")),
        },
        "product_outcome": {
            "level": "INTERPRETATION",
            "text": (f"{stage_row['product_outcome']} — {stage_row['outcome_detail']}" if stage_row
                     else "No single stage dominates the leading opportunity's evidence."),
            "stage": stage,
            "baseline": dec["baseline"],
            "max_headroom_pts": stage_row["max_headroom_pts"] if stage_row else None,
            "note": dec["headroom_note"],
        },
        "root_cause": {
            "level": "HYPOTHESIS",
            "text": lead["root_cause_chain"]["potential_root_cause"]["text"],
            "chain": {k: v["text"] for k, v in lead["root_cause_chain"].items()},
            "evidence": lead["root_cause_chain"]["potential_root_cause"]["evidence"],
            "confirm_in_research": "Is this the cause, or does the attempt already fail earlier, before the query is typed?",
        },
        "existing_workarounds": {
            "level": "OBSERVATION",
            "text": readable_list([w for w, _ in work]),
            "counts": work,
            "abandonment": abandoned,
            "evidence": _ev(c, ids, ("workaround",), {w for w, _ in work}),
        },
        "user_value": {
            "level": "INTERPRETATION",
            "text": ("Attempts are prompted by a concrete need with a deadline attached (a claim, a booking, a gift, a request from "
                     "someone else), so failure costs the user the task, not just the photo. "
                     f"Abandonment appears in {abandoned['numerator']}/{abandoned['denominator']} supporting records."),
            "evidence": goal_ev,
            "confirm_in_research": "What did the user do instead when they gave up, and what did that cost them?",
        },
        "business_rationale": {
            "level": "INTERPRETATION",
            "text": (f"The business metric is successful retrieval of vaguely remembered photos. Today {dec['baseline']['numerator']}/"
                     f"{dec['baseline']['denominator']} attempts in the corpus end in a confirmed find ({dec['baseline']['pct']}%), and "
                     f"{dec['unresolved']['numerator']} end unresolved. The stage with the largest recoverable share is "
                     f"{readable(dec['largest_headroom']['stage']) if dec['largest_headroom'] else '—'} "
                     f"(up to {dec['largest_headroom']['max_headroom_pts'] if dec['largest_headroom'] else 0} points). "
                     "A library that cannot return its own contents weakens the reason to keep adding to it."),
            "open_questions": [
                "How often does this happen per user per month? Public posts cannot answer this; product telemetry or a diary study can.",
                "Does retrieval failure change backup, storage-tier or app-open behaviour? That needs company data this study has no access to.",
            ],
        },
        "not_this_problem": {
            "level": "INTERPRETATION",
            "text": ("Not 'users find it difficult to search for old photos'. The evidence is narrower: users arrive with real clues "
                     f"({readable_list([l for l, _ in lead['top_remembered'][:3]])}) and still fail, because "
                     f"{readable_list([l for l, _ in lead['top_forgotten'][:3]])} is missing and the retrieval path needs it."),
        },
        "competing_explanation": {
            "level": "HYPOTHESIS",
            "text": (f"Runner-up: {readable(runner['opportunity'])}. {runner['description']}" if runner else "None."),
            "why_it_matters": "If interviews favour this instead, the product outcome to influence changes, and so does the segment to recruit.",
        },
        "evolution": [
            {"step": "Business metric", "level": "GIVEN",
             "text": "Increase the share of users who successfully retrieve a photo they remember but cannot precisely describe."},
            {"step": "Product outcomes", "level": "INTERPRETATION",
             "text": "Decomposed into the five things that must go right: recall → express → match → recognize → recover, plus whether the item is retrievable at all."},
            {"step": "AI-powered discovery", "level": "OBSERVATION",
             "text": (f"{b['overview']['total_records']} records analysed; {b['overview']['relevant']['numerator']} about retrieval; "
                      f"{b['overview']['retrieval_attempts']['numerator']} first-person attempts, each signal carrying a verbatim quote.")},
            {"step": "Observed user behaviour", "level": "OBSERVATION",
             "text": (f"Most-remembered clues: {readable_list([m['label'] for m in b['memory'][:3]])}; "
                      f"most-forgotten: {readable_list([m['label'] for m in b['forgotten'][:3]])}; "
                      f"breakdowns concentrate at {readable_list(dec['ranked_by_headroom'][:3])}.")},
            {"step": "Problem definition", "level": "DRAFT",
             "text": "Stated above, pending the 5–6 interviews. Each field carries either evidence or an open question, never an assumed finding."},
        ],
    }
