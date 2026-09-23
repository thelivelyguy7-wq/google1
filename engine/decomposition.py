"""Decomposition of "successful retrieval of a vaguely remembered photo" into user behaviours and product outcomes.

Success requires every node below to hold. A retrieval fails at the *first* node that does not. The nodes map onto the
four questions in the case brief plus two boundary nodes (recall, availability):

    D1 Recall     -> what does the user remember / forget?
    D2 Express    -> "Is the user unable to express what they remember?"
    D3 Understand -> "Does Google Photos fail to understand the clues they provide?"
    D4 Evaluate   -> "Are potentially relevant results difficult to evaluate?"
    D5 Refine     -> "Does the user struggle to refine an unsuccessful search?"
    D6 Available  -> is the photo in the searchable library at all? (boundary condition, our addition)

Evidence polarities per record and node:
    breakdown  the record states a difficulty at this node
    indirect   consistent with a failure here, but the record does not say where it failed
    effort     the user did extra work at this node
    intact     the record states the capability is retained / the step worked
    attempt    the user did something at this node; no outcome stated
Everything here is a count over records. Nothing in this module claims a real-world rate.
"""
from __future__ import annotations

import pandas as pd


def _in(series: pd.Series, *codes: str) -> pd.Series:
    return series.str.startswith(tuple(codes))


NODES = {
    "D1": dict(
        name="Recall", brief_question="What information do people actually remember, and what have they forgotten?",
        user_behavior="Holds partial context (people, place, story, look, roughly when) but lacks a precise identifier",
        product_outcome="n/a: this is the precondition the case starts from (photo exists, memory is incomplete)",
        opportunity="O6 Retrieval-path memory",
        proposed_measure="Share of retrieval attempts that start with contextual clues but no precise identifier (date, name, album, exact keyword)",
    ),
    "D2": dict(
        name="Express", brief_question="Is the user unable to express what they remember?",
        user_behavior="Turns memory into a query, filter or navigation step",
        product_outcome="The input the product receives carries the clues the user actually holds",
        opportunity="O1 Memory expression (with O2 Approximate-time narrowing and O8 Information discovery)",
        proposed_measure="Clues the user can state when prompted versus clues present in the first query (research); first-query length and clue types (production)",
    ),
    "D3": dict(
        name="Understand & match", brief_question="Does Google Photos fail to understand the clues they provide?",
        user_behavior="Submits clues and inspects what comes back",
        product_outcome="The intended photo appears among the candidates returned",
        opportunity="O4 Contextual matching",
        proposed_measure="Target-in-candidate-set rate for tasks with a known target (research); selected photo appearing on the first results page (production)",
    ),
    "D4": dict(
        name="Evaluate", brief_question="Are potentially relevant results difficult to evaluate?",
        user_behavior="Scans candidates and decides which one is the photo",
        product_outcome="The user confirms the right photo, quickly and with confidence",
        opportunity="O3 Candidate recognition / verification",
        proposed_measure="Candidates inspected before confirmation, time to confirm, wrong-photo confirmations, stated confidence (research); open-and-return counts (production)",
    ),
    "D5": dict(
        name="Refine", brief_question="Does the user struggle to refine an unsuccessful search?",
        user_behavior="Reformulates, switches strategy, browses, asks someone, or stops",
        product_outcome="A failed first attempt still ends in success, or in an informed stop",
        opportunity="O5 Retrieval recovery",
        proposed_measure="Success rate after reformulation, queries before success, abandonment after N unsuccessful queries (production); what prompted each change (research)",
    ),
    "D6": dict(
        name="Available", brief_question="Is the photo in the searchable library at all?",
        user_behavior="Asks another person, switches app or device, or gives up",
        product_outcome="Retrieval is possible: the photo exists in the library the user is searching",
        opportunity="O7 Corpus / access boundary",
        proposed_measure="Share of unsuccessful retrievals where the photo is absent from the library (needs a library audit in research)",
    ),
}

PRODUCTION_NOTE = "TBD, requires Google production data or primary research. These are candidate measures, not results."

# First-failing-node rule used when classifying every non-successful attempt in the task-based tests.
ATTRIBUTION_RULES = [
    ("D6", "The target photo is not in the participant's searchable library"),
    ("D1", "The participant cannot form any query and cannot describe any detail even when prompted neutrally"),
    ("D2", "The participant can later describe details that never reached a query (recall present, expression absent)"),
    ("D3", "The target never appears in any result set the participant saw"),
    ("D4", "The target appears in results the participant saw, but was not selected or was rejected"),
    ("D5", "Target found only after reformulation or a change of strategy (effortful success), or the participant stops after several tries with the underlying node recorded from the rules above"),
]


def node_masks(r: pd.DataFrame) -> dict:
    """node -> polarity -> boolean mask over relevant records."""
    mem, beh, clo = r["memory_code"], r["behavior_code"], r["closer_code"]
    none = pd.Series(False, index=r.index)
    m = {
        "D1": dict(
            breakdown=none,
            indirect=none,
            effort=none,
            intact=_in(clo, "C06") | _in(mem, "M09"),                          # states the photo exists
            attempt=none,
            condition=r["forgotten"] != "",                                      # names specific missing information
        ),
        "D2": dict(
            breakdown=r["express_barrier"] | _in(clo, "C04"),
            indirect=none,
            effort=none,
            intact=none,
            attempt=_in(beh, "B01", "B02", "B06"),                               # first-attempt input strategies
        ),
        "D3": dict(
            breakdown=none,                                                      # no record says the product misread the clues
            indirect=_in(beh, "B03", "B12", "B14"),                              # too many results / could not find / near miss
            effort=none,
            intact=_in(beh, "B03", "B04", "B13", "B14") | _in(clo, "C08"),      # candidates were surfaced (not proof of understanding)
            attempt=none,
        ),
        "D4": dict(
            breakdown=_in(beh, "B14") | _in(clo, "C08"),
            indirect=none,
            effort=_in(beh, "B04", "B11", "B13", "B16"),
            intact=_in(mem, "M05") | _in(clo, "C01"),                            # would recognise on sight
            attempt=none,
        ),
        "D5": dict(
            breakdown=_in(beh, "B08", "B10", "B12"),                             # ended unresolved / left the product
            indirect=none,
            effort=_in(beh, "B05", "B07", "B09", "B17", "B18"),
            intact=_in(beh, "B15"),                                              # found after several attempts
            attempt=none,
        ),
        "D6": dict(
            breakdown=none,                                                      # no record says the photo is missing
            indirect=_in(beh, "B08", "B10"),
            effort=none,
            intact=none,
            attempt=none,
        ),
    }
    return m


def summarize(r: pd.DataFrame) -> dict:
    E = len(r)
    out = {}
    for node, pol in node_masks(r).items():
        any_ev = pd.Series(False, index=r.index)
        for k, v in pol.items():
            if k != "condition":
                any_ev = any_ev | v
        entry = {k: int(v.sum()) for k, v in pol.items()}
        be = pol["breakdown"] | pol["effort"]
        entry["breakdown_or_effort"] = int(be.sum())
        entry["any_evidence"] = int(any_ev.sum())
        entry["no_evidence"] = E - int(any_ev.sum())
        entry["example_ids"] = {k: r.loc[v, "record_id"].sort_values().head(3).tolist() for k, v in pol.items() if int(v.sum())}
        entry.update({k: v for k, v in NODES[node].items()})
        out[node] = entry
    return out
