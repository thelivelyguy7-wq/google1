"""Business-metric decomposition (case study Part 2).

Successful retrieval of a vaguely remembered photo is decomposed into the stages a
user has to get through, so the PM can see *where* the metric is lost and how much
of it each stage could return.

Honesty rules:
  * The baseline is measured: found / attempts.
  * "Headroom" is an upper bound, not a forecast. It assumes every unsuccessful
    attempt that broke down at a stage would succeed if that stage never failed.
    It is labelled INTERPRETATION and carries that assumption with it.
  * Stages with no extracted breakdowns are shown as zero, not hidden.
"""
from __future__ import annotations

from collections import Counter

from .labels import readable
from .quant import ATTEMPT_DEF, Corpus, diverse_examples, rate

# Where each failure-taxonomy code sits in the retrieval journey. F is not a user
# stage at all: the data was missing or unsearchable, so it is reported separately.
STAGE_OF_FAILURE = {
    "A_memory_expression": "express",
    "B_system_understanding": "match",
    "C_retrieval": "match",
    "D_result_evaluation": "recognize",
    "E_refinement": "recover",
    "F_data_index_limitation": "data",
    "G_other": "other",
}

# "match" merges two failure codes, so the components stay visible: merging is a
# reporting choice about what public text can reliably separate, not a loss of evidence.
STAGE_COMPONENTS = {
    "match": [("B_system_understanding", "Query read differently than the user meant it"),
              ("C_retrieval", "Intended item never surfaced")],
}

# What has to be true at each stage, stated as the user's capability.
STAGE_CONDITION = {
    "recall": "The user remembers enough contextual information to identify the intended photo.",
    "express": "The user converts what they remember into a search attempt.",
    "match": "Photos surfaces candidates that correspond to the user's remembered clues.",
    "recognize": "The user can identify the intended photo among the candidates.",
    "recover": "After a failed attempt, the user can refine or change the search and continue.",
    "data": "The item, and the information needed to find it, exist in the library and are indexed.",
    "other": "Breakdowns outside the five stages and the data layer.",
}

# The product outcome that would move if the stage stopped failing, phrased as an
# outcome (what becomes true for users), never as a feature.
STAGE_OUTCOME = {
    "recall": ("Users start with something the system can act on",
               "More attempts begin with at least one clue the library can be searched by. Every attempt in this "
               "population passes this stage by definition: the user does remember something."),
    "express": ("Remembered context becomes a usable query",
                "More users turn what they remember into search terms without guessing the system's vocabulary."),
    "match": ("Remembered clues bring back the intended photo",
              "More queries are read as a whole description instead of matching one word, and more attempts "
              "surface the intended item at all."),
    "recognize": ("Users recognise the intended photo among candidates",
                  "More attempts end in recognition instead of comparing near-identical thumbnails."),
    "recover": ("A failed first attempt has a useful next step",
                "Fewer attempts end in exhaustive scrolling or abandonment after the first miss."),
    "data": ("Needed items and their context are retrievable at all",
             "Fewer attempts fail because the item or the information needed to find it is missing or unindexed."),
    "other": ("Other breakdowns", "Recurring breakdowns outside the A–F taxonomy."),
}

JOURNEY_ORDER = ["recall", "express", "match", "recognize", "recover"]
UNSUCCESSFUL = ("not_found", "abandoned", "partially_found", "uncertain")


def metric_decomposition(c: Corpus) -> dict:
    """Break 'successful retrieval' into stage outcomes, each sized from the evidence."""
    attempts = c.attempts
    n = len({a["record_id"] for a in attempts})
    found = sum(1 for a in attempts if a["payload"].get("success_status") == "found")
    unresolved = [a for a in attempts if a["payload"].get("success_status") in UNSUCCESSFUL]

    by_stage: dict[str, list] = {s: [] for s in JOURNEY_ORDER + ["data", "other"]}
    no_breakdown, unclear = [], []
    for a in attempts:
        stage = STAGE_OF_FAILURE.get(a["payload"].get("failure_stage"))
        if stage:
            by_stage[stage].append(a)
        elif a["payload"].get("failure_stage") == "none_observed":
            no_breakdown.append(a)
        else:
            unclear.append(a)

    difficulty = {j["stage"]: j["records_with_difficulty"] for j in c.journey()}
    stages = []
    for stage in JOURNEY_ORDER + ["data", "other"]:
        pop = by_stage[stage]
        lost = [a for a in pop if a["payload"].get("success_status") in UNSUCCESSFUL]
        opp = Counter(o for a in pop for o in (a["payload"].get("opportunity_areas") or []))
        name, outcome = STAGE_OUTCOME[stage]
        stages.append({
            "stage": stage,
            "in_journey": stage in JOURNEY_ORDER,
            "product_outcome": name,
            "outcome_detail": outcome,
            "condition": STAGE_CONDITION[stage],
            "components": _components(stage, pop, n, c),
            "breaks_here": rate(len({a["record_id"] for a in pop}), n, ATTEMPT_DEF, c.scope),
            "unresolved_here": rate(len({a["record_id"] for a in lost}), n, ATTEMPT_DEF, c.scope),
            # Upper bound on the business metric if this stage never failed (INTERPRETATION).
            "max_headroom_pts": round(100 * len(lost) / n, 1) if n else 0.0,
            "difficulty_reported": difficulty.get(stage),
            "opportunities": opp.most_common(3),
            "examples": diverse_examples(
                [c.evidence(s) for a in pop for s in c.signals_by_analysis[a["analysis_id"]] if s["kind"] == "failure"], 3),
        })

    ranked = sorted([s for s in stages if s["max_headroom_pts"] > 0], key=lambda s: -s["max_headroom_pts"])
    return {
        "business_metric": "Successful retrieval of a vaguely remembered photo",
        "definition": "An attempt counts as successful when the user reports identifying the intended item.",
        "baseline": {**rate(found, n, ATTEMPT_DEF, c.scope), "level": "OBSERVATION"},
        "unresolved": rate(len({a["record_id"] for a in unresolved}), n, ATTEMPT_DEF, c.scope),
        "no_breakdown_described": rate(len({a["record_id"] for a in no_breakdown}), n, ATTEMPT_DEF, c.scope),
        "breakdown_unclear": rate(len({a["record_id"] for a in unclear}), n, ATTEMPT_DEF, c.scope),
        "stages": stages,
        "ranked_by_headroom": [s["stage"] for s in ranked],
        "largest_headroom": ranked[0] if ranked else None,
        "headroom_note": ("INTERPRETATION. Headroom is the share of all attempts that broke down at this stage and did not "
                          "succeed: the most the success rate could rise if that stage never failed. It assumes nothing else "
                          "changes and that each attempt has a single decisive breakdown, so treat it as an upper bound for "
                          "prioritisation, not a forecast."),
        "levels": {"baseline": "OBSERVATION", "breaks_here": "OBSERVATION", "max_headroom_pts": "INTERPRETATION"},
    }


def _components(stage: str, pop: list, n: int, c: Corpus) -> list[dict]:
    """For a merged stage, the failure codes underneath it, so the merge stays auditable."""
    out = []
    for code, label in STAGE_COMPONENTS.get(stage, []):
        recs = {a["record_id"] for a in pop if a["payload"].get("failure_stage") == code}
        out.append({"code": code, "label": label, "breaks_here": rate(len(recs), n, ATTEMPT_DEF, c.scope)})
    return out


def stage_summary(dec: dict, stage: str) -> dict | None:
    return next((s for s in dec["stages"] if s["stage"] == stage), None)


def readable_stage(stage: str) -> str:
    return readable(stage) if stage not in STAGE_OUTCOME else stage.replace("data", "data & index").capitalize()
