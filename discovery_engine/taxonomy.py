"""Controlled vocabularies for the Discovery Engine.

Every list here is a *starting* taxonomy (spec §12-§17). Analyzers may propose new
labels; proposals are stored with a `proposed:` prefix so a PM can review them
before they are promoted into these lists.
"""

# The retrieval journey: five things that must go right for a vaguely remembered photo to be found.
# Each stage is a user capability, not a system component. "match" covers both reading the query as
# the user meant it and returning the intended item; public text rarely separates the two reliably.
JOURNEY_STAGES = ["recall", "express", "match", "recognize", "recover"]

RETRIEVAL_SCENARIOS = [
    "travel_memory", "food_restaurant_memory", "family_memory", "friend_memory",
    "event_memory", "wedding_memory", "work_memory", "document", "receipt",
    "medical_or_health_image", "screenshot", "purchase_related_image",
    "location_memory", "object_memory", "social_memory", "school_or_college_memory",
    "personal_memory", "video", "other",
]

MEMORY_SIGNALS = [
    "remembered_person", "remembered_place", "remembered_event", "remembered_occasion",
    "remembered_object", "remembered_activity", "remembered_trip",
    "remembered_time_approximation", "remembered_visual_appearance", "remembered_text",
    "remembered_relationship", "remembered_context", "remembered_emotion",
    "remembered_sequence", "remembered_social_context",
]

FORGOTTEN_INFORMATION = [
    "exact_date_unknown", "exact_location_unknown", "person_name_unknown",
    "event_name_unknown", "filename_unknown", "album_unknown", "exact_keyword_unknown",
    "exact_text_unknown", "exact_object_name_unknown", "metadata_unknown",
]

BEHAVIORS = [
    "retrieval_attempt", "successful_retrieval", "failed_retrieval", "abandoned_retrieval",
    "repeated_search", "query_refinement", "manual_browsing", "date_based_search",
    "location_based_search", "person_based_search", "album_based_search", "keyword_search",
    "natural_language_search", "visual_description", "contextual_description",
    "metadata_guessing", "external_workaround",
]

WORKAROUNDS = [
    "repeated_search", "synonym_search", "manual_scrolling", "date_browsing",
    "location_browsing", "album_browsing", "people_browsing", "filters",
    "external_search", "ask_another_person", "other_application", "return_later",
    "abandonment",
]

# §17 failure taxonomy
FAILURE_STAGES = {
    "A_memory_expression": "User remembers something but struggles to translate it into searchable information.",
    "B_system_understanding": "User provides a meaningful clue but the system appears not to interpret it correctly.",
    "C_retrieval": "The relevant photo does not appear or is insufficiently surfaced.",
    "D_result_evaluation": "The relevant photo may be present but the user struggles to recognise or distinguish it.",
    "E_refinement": "First attempt fails and the user does not know how to continue effectively.",
    "F_data_index_limitation": "Relevant information is unavailable, missing, inaccessible or insufficiently represented.",
    "G_other": "A recurring failure mode that does not fit the categories above.",
    "none_observed": "No failure is described.",
    "unclear": "A failure is implied but the stage cannot be determined from the text.",
}

SUCCESS_STATUS = ["found", "not_found", "partially_found", "uncertain", "abandoned", "not_stated"]

QUERY_ORIENTATION = [  # §16 "what users naturally formulate queries around"
    "what_happened", "where", "who", "what_they_saw", "why_taken",
    "approximate_when", "image_contents", "what_needed_for",
]

EPISTEMIC_LEVELS = ["OBSERVATION", "INSIGHT", "INTERPRETATION", "HYPOTHESIS", "OPPORTUNITY"]

EVIDENCE_STRENGTH = ["HIGH", "MEDIUM", "LOW", "DIRECTIONAL"]

# Candidate opportunity areas the analyzer may map to. These are problem spaces,
# never features (§26). New areas can be proposed with a `proposed:` prefix.
SEED_OPPORTUNITY_AREAS = {
    "context_to_query_translation": "Help users retrieve memories using contextual clues (events, relationships, experiences) they remember but cannot translate into searchable terms.",
    "approximate_time_anchoring": "Help users locate photos when they only remember time approximately or relative to another event.",
    "multi_clue_combination": "Help users narrow retrieval by combining several weak, partial clues that individually return too much or nothing.",
    "candidate_recognition": "Help users recognise the intended photo among many visually similar candidates.",
    "recovery_after_failed_search": "Help users know what to try next after an unsuccessful retrieval attempt, instead of falling back to exhaustive scrolling.",
    "text_in_image_recall": "Help users retrieve documents, receipts and screenshots when they remember what the content was about but not its exact words.",
    "index_coverage_gaps": "Address content that is not retrievable because the needed information is missing, unindexed or inaccessible.",
    "trust_in_search_completeness": "Help users judge whether a photo is absent from results versus absent from the library.",
}
