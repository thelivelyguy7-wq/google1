"""Behavioural retrieval segments (NextLeap PM model).

**Primary segmentation is binary, and only binary:** every first-person retrieval
attempt is either

  * Direct       user expresses a strong identifier, the query is precise, and the
                 photo is found with low effort, or
  * Contextual   user remembers the surrounding circumstances rather than a precise
                 identifier, so the query is built from several weaker clues and the
                 system has to connect them.

Person / event / location / visual / text are deliberately *not* separate primary
segments: they are memory clues used to characterize the Contextual population, not
axes to segment users by. Likewise "Candidate-heavy" and "Recovery-dependent" are not
primary segments - they describe *how a Contextual attempt actually played out*, so
they live in the Retrieval State lens below, not in the primary cut. Direct is a
narrow, precise rule; Contextual is everything else, by construction, which matches
the fact that contextual memory is the starting condition for almost every attempt.

**Secondary characterization** cuts across that binary split with three independent
lenses, each computed per attempt:

  1. Memory state        what the person still holds vs has lost (identifier held,
                          partial identifier, context only, nothing specific).
  2. Retrieval complexity how many kinds of clue have to be combined, and whether any
                          of them is a precise anchor: low (1-2 kinds, at least one
                          precise), medium (several kinds, or few with none precise),
                          high (3+ kinds, none precise - "multiple weak, ambiguous
                          clues").
  3. Retrieval state      how the attempt actually resolved: direct/low-effort,
                          candidate-heavy (too many/too-similar candidates),
                          recovery-dependent (first attempt failed, user changed
                          route), unresolved (no confident find, no stated cause), or
                          unavailable (the item was never in the searchable library).

Retrieval state absorbs what used to be two primary segments (Candidate-heavy,
Recovery), because the evidence that put an attempt there is unchanged: a search
that returns too many results, or a breakdown at telling similar candidates apart,
is Candidate-heavy; a first attempt that failed and a changed route is
Recovery-dependent. What changed is only that these are now states a Contextual (or,
rarely, a Direct) attempt can be in, not user segments in their own right.

TARGET_SEGMENT_HYPOTHESIS below is the standing hypothesis for primary research:
Contextual Retrieval users whose incomplete memories lead to candidate-heavy or
recovery-dependent retrieval. It is a hypothesis to validate, not a conclusion.
"""
from __future__ import annotations

from collections import Counter

ORDER = ["direct", "contextual"]

NAME = {
    "direct": "Direct Retrieval",
    "contextual": "Contextual Retrieval",
}

DEFINITION = {
    "direct": "User expresses a strong identifier; the query is precise, ambiguity is low, and the photo is found with little effort.",
    "contextual": "User remembers the surrounding context rather than a precise identifier; the query is built from several weaker clues that the system has to connect.",
}

# Where each segment sits on the five-stage journey (Recall -> Express -> Match -> Recognize -> Recover).
# Contextual spans the full range because candidate-heavy and recovery-dependent attempts - which used
# to be their own segments - are Contextual attempts now classified by their retrieval state.
STAGES = {
    "direct": ["recall", "express", "match", "recognize"],
    "contextual": ["express", "match", "recognize", "recover"],
}

# Clues that describe the circumstances of a photo rather than name it.
CONTEXT_CLUES = {
    "remembered_event", "remembered_occasion", "remembered_trip", "remembered_activity", "remembered_context",
    "remembered_relationship", "remembered_emotion", "remembered_visual_appearance", "remembered_time_approximation",
}
# Clues the library can be searched by directly when they are stated precisely.
IDENTIFIER_CLUES = {"remembered_person", "remembered_place", "remembered_text", "remembered_object"}
# Precise identifiers the user says they no longer have.
IDENTIFIER_GAPS = {
    "exact_date_unknown", "exact_location_unknown", "exact_text_unknown", "exact_object_name_unknown",
    "exact_keyword_unknown", "event_name_unknown", "album_unknown", "metadata_unknown", "person_name_unknown",
}
# A change of strategy after the first attempt. Abandonment is deliberately absent: giving up is an
# outcome, not a way of retrieving, and it is reported inside every segment instead.
RECOVERY_MOVES = {
    "manual_scrolling", "date_browsing", "people_browsing", "location_browsing", "album_browsing", "filters",
    "synonym_search", "repeated_search", "ask_another_person", "other_application", "external_search", "return_later",
}

# Searching by something the library indexes directly.
IDENTIFIER_STRATEGIES = {"keyword_search", "person_based_search", "date_based_search", "location_based_search",
                         "album_based_search"}

PRECEDENCE = ["direct", "contextual"]

RULES = {
    "direct": ("Found; one attempt; no breakdown described; no change of route; no missing identifier; and either a "
               "precisely stated person, place, text or object, or a search by keyword, person, date, place or album. "
               "A descriptive sentence typed into search counts as Contextual, not Direct."),
    "contextual": ("Everything that is not Direct: circumstantial clues (event, occasion, trip, activity, appearance, "
                   "rough time, relationship), a precise identifier the person says they have lost, or a scene "
                   "described in a sentence instead of named. This is the complement of Direct by construction, so "
                   "the two segments always sum to 100% of attempts."),
    "precedence": "An attempt is Direct only if it meets the Direct rule in full; every other attempt is Contextual.",
}

TARGET_SEGMENT_HYPOTHESIS = (
    "Contextual Retrieval users whose incomplete memories lead to candidate-heavy or recovery-dependent retrieval."
)

# Impact-mapping chain for this hypothesis (WHY -> WHO -> HOW -> WHAT). WHAT is deliberately left as a
# space of directions, not a choice: no solution is selected before HOW is validated in primary research.
IMPACT_MAP = {
    "why": "Increase successful retrieval of remembered-but-imprecisely-described photos.",
    "who": "Users engaging in Contextual Retrieval, especially those in a candidate-heavy or recovery-dependent state.",
    "how": ("The user needs to connect multiple contextual memories into a successful retrieval path without "
            "repeated search failure or manual candidate inspection."),
    "what_note": ("Solution space - not yet chosen. Only to be entered after HOW is validated by primary research. "
                 "Candidate directions to evaluate later, none selected: contextual query expansion, multi-clue "
                 "retrieval, conversational refinement, memory-based search assistance, temporal/contextual "
                 "narrowing, candidate explanation."),
}


def flags_for(a: dict, sigs: list[dict]) -> dict:
    """Behaviour and retrieval-state flags for one attempt, with the signals that triggered each (for audit)."""
    p = a["payload"]
    by_kind: dict[str, list[dict]] = {}
    for s in sigs:
        by_kind.setdefault(s["kind"], []).append(s)
    remembered = by_kind.get("remembered", [])
    gaps = [s for s in by_kind.get("forgotten", []) if s["label"] in IDENTIFIER_GAPS]
    context = [s for s in remembered if s["label"] in CONTEXT_CLUES or s.get("precision") == "approximate"]
    ident = [s for s in remembered if s["label"] in IDENTIFIER_CLUES and s.get("precision") == "exact"]
    moves = [s for s in by_kind.get("workaround", []) if s["label"] in RECOVERY_MOVES]
    refinements = by_kind.get("refinement", [])
    crowded = [s for s in by_kind.get("query", []) if str(s.get("precision", "")).endswith("too_many_results")]

    strategies = by_kind.get("strategy", [])
    described = [s for s in strategies if s["label"] == "natural_language_search"]
    id_search = [s for s in strategies if s["label"] in IDENTIFIER_STRATEGIES]
    found_query = [s for s in by_kind.get("query", []) if str(s.get("precision", "")).endswith("|found")]

    # Recovery-dependent means the *initial* attempt failed. A route change after a search that already
    # worked ("searched 'houseboat' and it popped up... I asked my sister too") is not recovering from anything.
    failed_query = [s for s in by_kind.get("query", [])
                    if str(s.get("precision", "")).split("|")[-1] in ("not_found", "wrong_results", "too_many_results")]
    initial_failed = bool(failed_query or p.get("failure_stage") not in (None, "none_observed", "unclear")
                          or p.get("success_status") in ("not_found", "abandoned", "partially_found", "uncertain"))
    changed_route = bool(moves or refinements or (p.get("attempt_count") or 0) >= 2 or p.get("failure_stage") == "E_refinement")
    recovery = changed_route and initial_failed
    candidate = bool(crowded or p.get("failure_stage") == "D_result_evaluation")
    contextual_signal = bool(context or (remembered and gaps) or described)
    # A descriptive sentence that worked is the system connecting context (Contextual), never Direct.
    direct = (p.get("success_status") == "found" and (p.get("attempt_count") or 1) <= 1
              and p.get("failure_stage") == "none_observed" and not gaps and not moves and not refinements
              and not crowded and not described and bool(ident or id_search or found_query))
    # The item was never searchable at all: a data/index limitation with no route change or crowding to explain instead.
    unavailable = p.get("failure_stage") == "F_data_index_limitation" and not (moves or refinements or crowded)
    # Ordered so the sentence that shows the behaviour comes before the bare query text.
    triggers = {
        "recovery": moves + refinements,
        "candidate_heavy": [s for s in by_kind.get("failure", []) if s["label"] == "D_result_evaluation"] + crowded,
        "contextual": context + gaps + described,
        "direct": id_search + ident + found_query,
    }
    return {"direct": direct, "contextual": contextual_signal, "candidate_heavy": candidate, "recovery": recovery,
            "triggers": triggers, "outside_library": unavailable}


def primary(flags: dict) -> str:
    """Direct if the attempt earns it in full; Contextual otherwise. Every attempt gets exactly one."""
    return "direct" if flags["direct"] else "contextual"


# ---------------------------------------------------------------------------
# Secondary segmentation. The Direct/Contextual cut is primary; these three lenses cut across it.
LENSES = {
    "memory_state": {
        "name": "Memory state",
        "question": "What does the person still hold about the photo?",
        "order": ["identifier_held", "partial_identifier", "context_only", "nothing_specific"],
        "labels": {
            "identifier_held": "Identifier held",
            "partial_identifier": "Partial identifier",
            "context_only": "Context only",
            "nothing_specific": "Nothing specific stated",
        },
        "definitions": {
            "identifier_held": "Remembers a person, place, text or object precisely, and names no identifier as lost.",
            "partial_identifier": "Holds one precise anchor (a person, an object) but has lost another the search needs, usually the date or place.",
            "context_only": "Remembers circumstances - the occasion, what it looked like, roughly when - but no precise identifier.",
            "nothing_specific": "Neither the post nor anything typed shows a remembered clue; only the need or the outcome is stated.",
        },
        "rule": ("From the remembered and forgotten signals, plus what the person typed: a precisely stated person, place, text or "
                 "object counts as an identifier; a forgotten date, location, text, name, album or metadata counts as a lost "
                 "identifier; what a query describes (who, where, roughly when, what it looked like) counts as context held."),
    },
    "complexity": {
        "name": "Retrieval complexity",
        "question": "How many clues does the system have to combine, and how ambiguous are they?",
        "order": ["low", "medium", "high", "no_clue"],
        "labels": {"low": "Low complexity", "medium": "Medium complexity", "high": "High complexity", "no_clue": "No clue stated"},
        "definitions": {
            "low": "One or two relatively strong clues, at least one a precise anchor (a name, a place, a date). Example: \"Photo of Rahul at Goa.\"",
            "medium": "Several clues in play, either a strong anchor combined with more circumstantial detail, or a couple of weak clues alone. Example: \"Rahul, Goa, beach, sunset, around 2023.\"",
            "high": "Three or more clues, none of them a precise anchor - multiple weak, ambiguous clues that must all be intersected. Example: \"That café we went to after the beach with the blue chairs, sometime during our Goa trip.\"",
            "no_clue": "No remembered clue is stated, so there is nothing to combine.",
        },
        "rule": ("Distinct kinds of clue in the attempt, remembered or typed (person, place, event, object, appearance, rough time, "
                 "text...), combined with whether any of them is a precise anchor. More kinds with no anchor means more, weaker "
                 "constraints to intersect; keyword search matches words, not combinations."),
    },
    "retrieval_state": {
        "name": "Retrieval state",
        "question": "How did the attempt actually play out?",
        "order": ["direct_low_effort", "candidate_heavy", "recovery_dependent", "unresolved", "unavailable"],
        "labels": {
            "direct_low_effort": "Direct / low-effort", "candidate_heavy": "Candidate-heavy",
            "recovery_dependent": "Recovery-dependent", "unresolved": "Unresolved", "unavailable": "Unavailable",
        },
        "definitions": {
            "direct_low_effort": "Finds the relevant photo without a crowded result set, a changed route, or a breakdown.",
            "candidate_heavy": "The system returns multiple plausible candidates and the user struggles to narrow or recognise the intended one.",
            "recovery_dependent": "The first attempt fails and the user changes strategy - reformulates, browses, filters, asks someone, or tries elsewhere - to continue.",
            "unresolved": "The user cannot confidently find the photo, and no data/index limitation or changed route explains why.",
            "unavailable": "The photo is not actually in the searchable library (never backed up, on another device or account, not indexed).",
        },
        "rule": ("Assigned by precedence from the extracted signals, most specific cause first: a data/index limitation is "
                 "Unavailable; otherwise a crowded or hard-to-distinguish result set is Candidate-heavy; otherwise a changed "
                 "route after a failed first attempt is Recovery-dependent; a clean find is Direct/low-effort; anything else "
                 "that neither resolves nor names a cause is Unresolved."),
    },
}


# What a typed query shows the person held. A search for "green fireworks over pool" is memory of what
# the photo looked like even when the post never narrates it; without this, short success posts read as
# "nothing remembered" and the lens inverts. These count as context, never as identifiers.
QUERY_CLUE = {"who": "remembered_person", "where": "remembered_place", "approximate_when": "remembered_time_approximation",
              "what_they_saw": "remembered_visual_appearance", "image_contents": "remembered_object"}


def _typed_clues(sigs: list[dict]) -> set[str]:
    out = set()
    for s in sigs:
        if s["kind"] == "query":
            for part in str(s.get("precision") or "").split("|")[0].split(","):
                if part in QUERY_CLUE:
                    out.add(QUERY_CLUE[part])
    return out


def secondary(a: dict, sigs: list[dict], flags: dict) -> dict:
    """Memory state, retrieval complexity and retrieval state for one attempt."""
    p = a["payload"]
    remembered = [s for s in sigs if s["kind"] == "remembered"]
    typed = _typed_clues(sigs)
    gaps = [s for s in sigs if s["kind"] == "forgotten" and s["label"] in IDENTIFIER_GAPS]
    ident_labels = {s["label"] for s in remembered if s["label"] in IDENTIFIER_CLUES and s.get("precision") == "exact"}
    # Typed clues are context, never identifiers, even when the label they map to can also be an identifier.
    context_labels = ({s["label"] for s in remembered if s["label"] in CONTEXT_CLUES or s.get("precision") == "approximate"}
                       | typed) - ident_labels

    if ident_labels and not gaps:
        memory = "identifier_held"
    elif ident_labels:
        memory = "partial_identifier"
    elif remembered or typed:
        memory = "context_only"
    else:
        memory = "nothing_specific"

    total_kinds = len(ident_labels | context_labels)
    if total_kinds == 0:
        complexity = "no_clue"
    elif total_kinds <= 2 and ident_labels:
        complexity = "low"
    elif total_kinds >= 3 and not ident_labels:
        complexity = "high"
    else:
        complexity = "medium"

    if flags["outside_library"]:
        retrieval_state = "unavailable"
    elif flags["candidate_heavy"]:
        retrieval_state = "candidate_heavy"
    elif flags["recovery"]:
        retrieval_state = "recovery_dependent"
    elif p.get("success_status") == "found":
        retrieval_state = "direct_low_effort"
    else:
        retrieval_state = "unresolved"

    return {"memory_state": memory, "complexity": complexity, "retrieval_state": retrieval_state}


def classify(c) -> dict[str, dict]:
    """record_id -> {"primary": seg, "flags": {...}, "secondary": {...}, "analysis": a}. One entry per attempt record."""
    out = {}
    for a in c.attempts:
        if a["record_id"] in out:
            continue
        sigs = c.signals_by_analysis[a["analysis_id"]]
        f = flags_for(a, sigs)
        out[a["record_id"]] = {"primary": primary(f), "flags": f, "secondary": secondary(a, sigs, f), "analysis": a}
    return out


def distribution(cls: dict[str, dict]) -> Counter:
    return Counter(v["primary"] for v in cls.values())
