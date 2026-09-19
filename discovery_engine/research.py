"""Research fit per behavioural segment (case study Part 3).

Choosing a segment to interview is not only about who hurts most. It is also about
whether you can *recruit* them, whether the behaviour can be *observed* in a session,
what the session may safely *look at*, and what retrieval states its attempts land in.

Each field here is either measured from the corpus (content sensitivity, retrieval-state
mix) or stated as a rule tied to the segment's definition (recruiting, observability,
session shape). Rules are exposed so the PM can disagree with them.

The primary segments are Direct and Contextual only. Candidate-heavy and
recovery-dependent attempts are Contextual attempts in a particular retrieval state
(see behavior_segments.LENSES["retrieval_state"]), not segments of their own, so the
session guidance for Contextual below is written to cover both mechanisms.
"""
from __future__ import annotations

from .quant import Corpus, rate

# Content that a participant may not want on a shared screen. Measured as a share of the
# segment's records; the consequence for the session is a method judgement, not a finding.
SENSITIVE_SCENARIOS = {"medical_or_health_image", "document", "receipt", "purchase_related_image", "work_memory"}

SENSITIVITY_RULE = ("Share of the segment's attempts about health images, documents, receipts, purchase references "
                    "or work material. Above 40% the session should not ask for a screen share.")

# The role each primary segment plays in a 5-6 person study, and how to find its members.
ROLE = {
    "direct": ("Contrast case",
               "The success path the metric aims for. One session shows what a strong identifier looks like when it "
               "works, which is exactly what Contextual attempts lack."),
    "contextual": ("Core of the study",
                   "The problem as defined: real clues, no identifier, and the system must connect them. Spans several "
                   "retrieval states - candidate-heavy (search returned plausible candidates but recognition failed), "
                   "recovery-dependent (first attempt failed, user changed route), unresolved and unavailable - so plan "
                   "for more than one mechanism inside this one segment."),
}

RECRUITING = {
    "direct": ("Screen on a recent quick find",
               "Ask for the last time they found a specific old photo quickly. Qualifies when it took one search, "
               "by a name, a face, a place, text in the image, or a date they knew."),
    "contextual": ("Screen on what they remembered",
                   "Ask what they remembered about a photo they looked for. Qualifies when they describe circumstances "
                   "(who, where, what was happening, what it looked like) rather than a name, date or text. Use the "
                   "retrieval-state qualifiers below to steer the mix toward candidate-heavy or recovery-dependent cases."),
}

OBSERVABILITY = {
    "live": ("Observable live", "The behaviour can be produced in the session on the participant's own library."),
    "mixed": ("Partly observable", "A fresh attempt can be observed, but past episodes that ended in giving up can only be recounted."),
}
OBSERVABLE = {"direct": "live", "contextual": "live"}

SESSION_EMPHASIS = {
    "direct": "Contrast case, 0-1 sessions. Capture what made the identifier strong: that is the thing Contextual attempts are missing.",
    "contextual": "Weight the session to memory elicitation and the unaided attempt. The clue delta (held vs typed vs what the system needed) is the primary analysis; use the retrieval-state screener to also capture candidate-heavy or recovery-dependent moments.",
}

QUALIFIER = {
    "direct": ("Think of the last time you found a specific old photo quickly. What did you search for, and how long did it take? "
               "(qualifies: one search, by a name, face, place, text or known date)"),
    "contextual": ("What did you remember about the photo when you started looking? (open question; qualifies when the answer "
                   "is circumstances - who, where, what was happening, what it looked like - rather than a name, date or text)"),
}

# Same shape, one level deeper: role/recruiting/observability/session/qualifier per Retrieval State,
# for drilling into the Contextual segment (the target-segment hypothesis names candidate-heavy and
# recovery-dependent specifically). Direct-low-effort and Contextual above cover the same ground at the
# primary-segment level; these exist so the PM can recruit for a specific mechanism instead.
STATE_ROLE = {
    "direct_low_effort": ("Contrast case", "A clean find, with or without a precise identifier. Shows the low-effort baseline the other states depart from."),
    "candidate_heavy": ("Distinct mechanism", "Search did its job and returned plausible candidates; the failure is recognition, not retrieval."),
    "recovery_dependent": ("Where the effort goes", "The first try failed and the user changed route. Shows what people do when search does not connect, and what it costs them."),
    "unresolved": ("Unexplained failure", "No confident find and no stated cause (not a crowded result set, not a changed route, not a data limitation). Worth understanding what the post leaves out."),
    "unavailable": ("Out of scope for a search fix", "The item was never in the searchable library. Useful as a boundary case: confirms which failures a retrieval change cannot touch."),
}
STATE_RECRUITING = {
    "direct_low_effort": ("Screen on a recent quick find", "Ask for the last time they found a specific old photo quickly."),
    "candidate_heavy": ("Screen on what came back", "Ask what the search showed them. Qualifies when it returned many results or many similar photos and they struggled to tell which one was the one."),
    "recovery_dependent": ("Screen on what they did next", "Ask what they did when the first search did not work. Qualifies when they changed route: scrolled, browsed by date, place, person or album, tried other words, used another app, or asked someone."),
    "unresolved": ("Screen on giving up without a clear reason", "Ask about a time they stopped looking without knowing why the search did not work."),
    "unavailable": ("Screen on knowing it wasn't there", "Ask about a time they realised the photo was never backed up, on another device, or otherwise not in the library."),
}
STATE_OBSERVABLE = {"direct_low_effort": "live", "candidate_heavy": "live", "recovery_dependent": "mixed", "unresolved": "mixed", "unavailable": "mixed"}
STATE_SESSION_EMPHASIS = {
    "direct_low_effort": "Contrast case, 0-1 sessions. Capture what made the find effortless.",
    "candidate_heavy": "Weight the live attempt to the results screen: time to recognise, how far they scroll, whether they pass over the target and come back.",
    "recovery_dependent": "Let the first attempt fail naturally and do not rescue it. Record each change of route and what prompted it; use the walkthrough for recoveries that ended in giving up.",
    "unresolved": "Ask what they think went wrong, but weight the analysis to the evidence, not the guess.",
    "unavailable": "Confirm how they know it isn't there (checked another device, remembers not backing it up) rather than assuming.",
}
STATE_QUALIFIER = {
    "direct_low_effort": "Think of the last time you found a specific old photo quickly. What did you search for, and how long did it take?",
    "candidate_heavy": "When you searched, what came back? (qualifies: many results or many similar photos, and trouble telling which one was the one)",
    "recovery_dependent": "When the first search did not work, what did you do next? (qualifies: scrolled, browsed by date, place, person or album, tried other words, used another app, or asked someone)",
    "unresolved": "Tell me about a time you stopped looking for a photo without being sure why the search did not work.",
    "unavailable": "Tell me about a time you realised a photo you wanted just wasn't going to be in your library.",
}


def _session_shape(key: str, sensitivity_level: str, emphasis: dict) -> dict:
    changes = [emphasis[key]]
    if sensitivity_level == "high":
        changes.append("No screen share. The participant narrates and reports what they see, and the moderator records "
                       "queries and outcomes only. Never ask to open a document, receipt or health image.")
    elif sensitivity_level == "medium":
        changes.append("Offer the screen share as opt-in per episode, and let the participant skip any result they would rather not show.")
    else:
        changes.append("Screen share is usually acceptable; still confirm per episode and let them skip anything.")
    return {"level": "INTERPRETATION", "changes": changes}


def _screener(key: str, sensitivity_level: str, qualifier: dict) -> list[str]:
    q = ["In the last 3 months, have you looked for a specific photo, video, screenshot or document on your phone? (must be yes)",
         qualifier[key],
         "Roughly how many photos are in your library, and how far back does it go? (capture only, do not exclude)",
         "Do you use Google Photos on Android, iPhone, or the web? (capture; recruit a mix)",
         "Have you worked in photography, search or machine learning? (exclude: they narrate the system, not the memory)"]
    if sensitivity_level in ("high", "medium"):
        q.append("This session may involve personal material. Are you comfortable describing what you searched for "
                 "without showing us the photo itself? (must be yes; nobody is asked to show sensitive content)")
    return q


def research_fit(c: Corpus, segs: list[dict]) -> dict[str, dict]:
    """Per-primary-segment role, recruiting, observability, sensitivity, screener and session shape."""
    fit = {}
    for s in segs:
        key, name = s["key"], s["segment"]
        ids = set(s["record_ids"])
        sensitive = {a["record_id"] for a in c.attempts
                     if a["record_id"] in ids and a["payload"].get("retrieval_scenario") in SENSITIVE_SCENARIOS}
        sens_rate = rate(len(sensitive), len(ids), f"attempts in '{name}'", c.scope)
        level = "high" if (sens_rate["pct"] or 0) >= 40 else "medium" if (sens_rate["pct"] or 0) >= 15 else "low"
        obs = OBSERVABLE[key]
        role_head, role_why = ROLE[key]
        rec_head, rec_why = RECRUITING[key]
        obs_head, obs_why = OBSERVABILITY[obs]
        fit[name] = {
            "role": {"headline": role_head, "why": role_why},
            "sensitivity": {"level": level, "rate": sens_rate, "rule": SENSITIVITY_RULE, "definitional": False,
                            "means": {"high": "Session runs without a screen share.",
                                      "medium": "Screen share is opt-in, per episode.",
                                      "low": "Screen share is usually fine; still ask each time."}[level]},
            "observability": {"key": obs, "headline": obs_head, "why": obs_why},
            "recruitability": {"headline": rec_head, "why": rec_why},
            # How this segment's attempts split across retrieval states (candidate-heavy, recovery-dependent, ...).
            "retrieval_states": s.get("retrieval_states", {}),
            "screener": _screener(key, level, QUALIFIER),
            "session_shape": _session_shape(key, level, SESSION_EMPHASIS),
            "sample_note": ("Evidence base is small, so treat this segment's rates as directional when you brief it."
                            if s["records"] < 30 else ""),
        }
    return fit


# Same shape, for the scenario-cluster axis (Part 3, extended): role/recruiting/observability/session/
# qualifier per cluster, so a PM choosing this axis instead of Direct/Contextual gets the same kind of
# guidance, grounded in why each cluster is or isn't a good primary research target.
CLUSTER_ROLE = {
    "time_place_experience": ("Core of the study",
        "The largest cluster (38% of attempts) and the closest match to the strategic goal: real experiences "
        "remembered, exact time or place lost. Breaks mostly at picking the right photo out of the results, "
        "which a live session can observe directly."),
    "object_document_text": ("Severity contrast",
        "Smaller but the most severe cluster (highest unsuccessful rate of any group): the memory often can't "
        "even become a query, because the missing piece is usually literal text on the item. A genuinely "
        "different failure mechanism from Time/Place-Approximate, worth 1-2 seats as a deliberate contrast."),
    "indexing_technical": ("Not recommended as primary",
        "Real, well-evidenced, but the dominant breakdown is a data/index limitation outside the user's memory "
        "journey. A session here mostly confirms 'it wasn't indexed' rather than revealing a memory-behaviour "
        "gap; treat as its own infrastructure opportunity, not a segment to recruit against."),
}
CLUSTER_RECRUITING = {
    "time_place_experience": ("Screen on a recent trip, meal or event photo",
        "Ask for the last time they looked for a photo from a trip, meal, event or occasion. Qualifies when "
        "they remember the experience but had to search, browse or scroll to find or confirm it."),
    "object_document_text": ("Screen on a document, receipt or item photo",
        "Ask for the last time they looked for a photo of a document, receipt, item or health-related image. "
        "Qualifies when they remember roughly what it was and when, but not the exact text or name on it."),
    "indexing_technical": ("Screen on a photo that turned out to be missing",
        "Ask about a time a photo they expected to find wasn't there at all. Useful only as a boundary case, "
        "not for the core study."),
}
CLUSTER_SESSION_EMPHASIS = {
    "time_place_experience": "Weight the session to the results screen: once candidates appear, watch how they narrow to the intended one, and what the query missed on the first try.",
    "object_document_text": "Weight the session to memory elicitation before any device is touched: the key question is whether the person can produce a searchable query at all from what they remember.",
    "indexing_technical": "Short session, if run at all: confirm the item's absence and how they found out, rather than a full retrieval walkthrough.",
}
CLUSTER_QUALIFIER = {
    "time_place_experience": "Think of the last time you looked for a photo from a trip, a meal out, or an event. What did you remember about it, and what did you search first?",
    "object_document_text": "Think of the last time you looked for a photo of a document, receipt, or item you'd photographed. What did you remember about it, and what did you type to search?",
    "indexing_technical": "Tell me about a time a photo you expected to find in your library just wasn't there.",
}
CLUSTER_OBSERVABLE = {"time_place_experience": "live", "object_document_text": "live", "indexing_technical": "mixed"}


def research_fit_scenario_clusters(c: Corpus, clusters: list[dict]) -> dict[str, dict]:
    """Per-scenario-cluster role, recruiting, observability, sensitivity, screener and session shape.

    Same shape as research_fit() so the research brief can read either axis interchangeably.
    """
    fit = {}
    for s in clusters:
        key, name = s["key"], s["segment"]
        ids = set(s["record_ids"])
        sensitive = {a["record_id"] for a in c.attempts
                     if a["record_id"] in ids and a["payload"].get("retrieval_scenario") in SENSITIVE_SCENARIOS}
        sens_rate = rate(len(sensitive), len(ids), f"attempts in '{name}'", c.scope)
        level = "high" if (sens_rate["pct"] or 0) >= 40 else "medium" if (sens_rate["pct"] or 0) >= 15 else "low"
        obs = CLUSTER_OBSERVABLE[key]
        role_head, role_why = CLUSTER_ROLE[key]
        rec_head, rec_why = CLUSTER_RECRUITING[key]
        obs_head, obs_why = OBSERVABILITY[obs]
        fit[name] = {
            "role": {"headline": role_head, "why": role_why},
            "sensitivity": {"level": level, "rate": sens_rate, "rule": SENSITIVITY_RULE, "definitional": key == "object_document_text",
                            "means": {"high": "Session runs without a screen share.",
                                      "medium": "Screen share is opt-in, per episode.",
                                      "low": "Screen share is usually fine; still ask each time."}[level]},
            "observability": {"key": obs, "headline": obs_head, "why": obs_why},
            "recruitability": {"headline": rec_head, "why": rec_why},
            "screener": _screener(key, level, CLUSTER_QUALIFIER),
            "session_shape": _session_shape(key, level, CLUSTER_SESSION_EMPHASIS),
            "sample_note": ("Evidence base is small, so treat this cluster's rates as directional when you brief it."
                            if s["records"] < 30 else ""),
        }
    return fit


def research_fit_by_state(c: Corpus, states: list[dict]) -> dict[str, dict]:
    """Same shape as research_fit, one level deeper: per Retrieval State, for drilling into Contextual."""
    fit = {}
    for s in states:
        key, name = s["key"], s["state"]
        ids = set(s["record_ids"])
        sensitive = {a["record_id"] for a in c.attempts
                     if a["record_id"] in ids and a["payload"].get("retrieval_scenario") in SENSITIVE_SCENARIOS}
        sens_rate = rate(len(sensitive), len(ids), f"attempts in '{name}'", c.scope)
        level = "high" if (sens_rate["pct"] or 0) >= 40 else "medium" if (sens_rate["pct"] or 0) >= 15 else "low"
        obs = STATE_OBSERVABLE[key]
        role_head, role_why = STATE_ROLE[key]
        rec_head, rec_why = STATE_RECRUITING[key]
        obs_head, obs_why = OBSERVABILITY[obs]
        fit[name] = {
            "role": {"headline": role_head, "why": role_why},
            "sensitivity": {"level": level, "rate": sens_rate, "rule": SENSITIVITY_RULE, "definitional": False,
                            "means": {"high": "Session runs without a screen share.",
                                      "medium": "Screen share is opt-in, per episode.",
                                      "low": "Screen share is usually fine; still ask each time."}[level]},
            "observability": {"key": obs, "headline": obs_head, "why": obs_why},
            "recruitability": {"headline": rec_head, "why": rec_why},
            "primary_mix": s.get("primary_mix", []),
            "screener": _screener(key, level, STATE_QUALIFIER),
            "session_shape": _session_shape(key, level, STATE_SESSION_EMPHASIS),
            "sample_note": ("Evidence base is small, so treat this state's rates as directional when you brief it."
                            if s["records"] < 30 else ""),
        }
    return fit
