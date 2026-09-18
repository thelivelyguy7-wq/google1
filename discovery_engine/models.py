"""Data contracts.

Two strictly separated layers (spec §9-§10):
  * RawRecord  - RAW EVIDENCE exactly as collected. Never rewritten by analysis.
  * ChunkAnalysis / Signal - AI INTERPRETATION. Every signal must carry a verbatim
    quote from the raw text; the validator marks quotes that cannot be found.
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class RawRecord(BaseModel):
    record_id: str
    source: str                          # e.g. "reddit", "google_play", "manual_csv"
    platform: str                        # e.g. "reddit/r/googlephotos", "android"
    source_url: Optional[str] = None
    source_id: Optional[str] = None
    title: Optional[str] = None
    text: str
    thread_context: Optional[str] = None
    parent_text: Optional[str] = None
    replies: list[str] = Field(default_factory=list)
    engagement: dict = Field(default_factory=dict)
    created_at: Optional[str] = None     # source timestamp, ISO-8601 if known
    retrieved_at: Optional[str] = None
    author_hash: Optional[str] = None    # salted hash only - never raw usernames
    is_synthetic: bool = False
    dataset: str = "default"


# ---------------------------------------------------------------------------
# AI interpretation schema (sent to Claude as a JSON schema)
# ---------------------------------------------------------------------------

Approx = Literal["exact", "approximate", "not_applicable"]


class Signal(BaseModel):
    label: str = Field(description="Taxonomy label, or 'proposed:<snake_case>' if no existing label fits.")
    value: str = Field(description="Short neutral description of what the text says (<= 20 words). No speculation.")
    quote: str = Field(description="VERBATIM contiguous span copied from the source text that supports this signal.")
    precision: Approx = Field(description="Whether the remembered/used clue is exact or approximate.")


class QueryAttempt(BaseModel):
    query_text: str = Field(description="The query as the user reports it; empty string if not stated.")
    quote: str = Field(description="VERBATIM span containing or describing the query.")
    query_type: Literal["natural_language", "keyword", "metadata", "visual_description",
                        "contextual_description", "person", "location", "date", "unknown"]
    orientation: list[Literal["what_happened", "where", "who", "what_they_saw", "why_taken",
                              "approximate_when", "image_contents", "what_needed_for"]]
    outcome: Literal["found", "not_found", "wrong_results", "too_many_results", "unclear"]


class JourneyStep(BaseModel):
    stage: Literal["recall", "express", "match", "recognize", "recover", "other"]
    observation: str = Field(description="What observably happened at this stage, from the text only.")
    difficulty: bool
    quote: str


class ChunkAnalysis(BaseModel):
    # --- relevance classifier -------------------------------------------
    relevant: bool = Field(description="True only if the text concerns finding/retrieving existing photos, videos, screenshots or documents in a photo library.")
    relevance_reason: str
    perspective: Literal["first_person_experience", "second_hand_report", "advice_or_answer",
                         "opinion_or_feature_request", "other"]
    describes_retrieval_attempt: bool = Field(description="True only if an actual attempt to find a specific item is described.")
    # --- scenario ----------------------------------------------------------
    retrieval_scenario: str
    retrieval_object: Literal["photo", "video", "screenshot", "document_or_receipt", "multiple", "unknown"]
    success_status: Literal["found", "not_found", "partially_found", "uncertain", "abandoned", "not_stated"]
    # --- memory & forgotten ------------------------------------------------
    remembered_information: list[Signal]
    forgotten_information: list[Signal]
    forgotten_info_blocks_retrieval: Literal["yes", "no", "unclear", "not_applicable"]
    # --- search behaviour --------------------------------------------------
    queries: list[QueryAttempt]
    search_strategies: list[Signal]
    query_refinements: list[Signal]
    attempt_count: Optional[int] = Field(description="Number of attempts if stated or countable; null otherwise.")
    # --- failure ------------------------------------------------------------
    failure_stage: str = Field(description="One of the failure taxonomy keys.")
    failure_reason: str
    failure_quote: str
    journey: list[JourneyStep]
    # --- behaviour & workarounds -------------------------------------------
    user_behaviors: list[Signal]
    workarounds: list[Signal]
    expectations: list[Signal] = Field(description="What the user expected the system to do, only if stated.")
    # --- segment / JTBD -----------------------------------------------------
    user_goal: str
    segment_signals: list[Signal] = Field(description="Behavioural/usage signals e.g. library size, device, frequency of search. Never demographics unless explicitly stated and relevant.")
    jtbd_signal: str = Field(description="INTERPRETATION: a WHEN/BUT/HELP ME/SO fragment grounded in this text, or empty.")
    # --- synthesis hooks ----------------------------------------------------
    opportunity_areas: list[str]
    counter_evidence: list[Signal] = Field(description="Content that challenges common assumptions, e.g. vague search that succeeded, failure caused by something other than memory.")
    interpretation: str = Field(description="INTERPRETATION (not fact) of what explains the behaviour. Mark uncertainty.")
    supplementary_sentiment: Literal["negative", "neutral", "positive", "mixed"]
    confidence: float = Field(description="0-1 confidence in this overall extraction.")


class RelevanceResult(BaseModel):
    relevant: bool
    reason: str
    confidence: float
