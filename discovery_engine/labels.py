"""Human-readable names for internal labels.

Data fields keep raw labels (they are join keys and filter values). Anything a
person reads (report narrative, hypotheses, research brief) goes through
`readable()` / `prettify()` so the PM never sees `F_data_index_limitation`.
"""
from __future__ import annotations

import re

FAILURE = {
    "A_memory_expression": "can't express the memory (A)",
    "B_system_understanding": "search misreads the clue (B)",
    "C_retrieval": "photo never surfaces (C)",
    "D_result_evaluation": "can't pick out the right photo (D)",
    "E_refinement": "stuck after the first miss (E)",
    "F_data_index_limitation": "data missing or unsearchable (F)",
    "G_other": "other breakdown (G)",
    "none_observed": "no breakdown described",
    "unclear": "breakdown unclear",
}
OPPORTUNITY = {
    "context_to_query_translation": "Turning context into search terms",
    "approximate_time_anchoring": "Anchoring a rough sense of time",
    "multi_clue_combination": "Combining several weak clues",
    "candidate_recognition": "Recognising the right photo",
    "recovery_after_failed_search": "Recovering after a failed search",
    "text_in_image_recall": "Recalling what the text said",
    "index_coverage_gaps": "Missing or unsearchable data",
    "trust_in_search_completeness": "Trusting \"no results\"",
}
SPECIAL = {
    "food_restaurant_memory": "food/restaurant", "medical_or_health_image": "medical/health image",
    "school_or_college_memory": "school/college", "purchase_related_image": "purchase-related image",
    "document_or_receipt": "document/receipt", "partially_found": "partly found",
    "google_photos_community": "Google Photos Community", "google_play": "Google Play", "app_store": "App Store",
    "social_media": "social media", "youtube": "YouTube", "reddit": "Reddit", "forums": "forums",
}


def readable(label) -> str:
    if label is None or label == "":
        return "—"
    s = str(label)
    if s in FAILURE:
        return FAILURE[s]
    if s in OPPORTUNITY:
        return OPPORTUNITY[s]
    if s in SPECIAL:
        return SPECIAL[s]
    proposed = s.startswith("proposed:")
    core = s.removeprefix("proposed:").removeprefix("remembered_")
    core = re.sub(r"_unknown$", "", core)
    core = re.sub(r"_memory$", "", core)
    return ("proposed: " if proposed else "") + core.replace("_", " ")


def readable_list(labels, sep=", ") -> str:
    return sep.join(readable(x) for x in labels) or "—"


_TOKEN = re.compile(r"\b(?:[A-G]_[a-z_]+|[a-z]+(?:_[a-z]+)+)\b")


def prettify(text: str) -> str:
    """Rewrite raw label tokens inside free text; leaves numbers and wording untouched."""
    return _TOKEN.sub(lambda m: readable(m.group(0)), str(text or ""))


def counts_phrase(counts: dict) -> str:
    """{'not_found': 33, 'found': 19} -> 'not found 33, found 19' (largest first)."""
    return ", ".join(f"{readable(k)} {v}" for k, v in sorted(counts.items(), key=lambda kv: -kv[1]))
