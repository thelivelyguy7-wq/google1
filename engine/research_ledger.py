"""Primary research ledger.

This module provides the schema and ingestion logic for the real-world research data.
The ledger tracks participant data across the discovery phases:
participant ID, stage, node, code, verbatim, method.
"""
from typing import Literal, Optional
from pydantic import BaseModel, Field
import pandas as pd

# Stage corresponds to the journey stages or interview sections
Stage = Literal["screener", "recent_incident", "task_test", "follow_up"]
# Node corresponds to D1-D6 decomposition framework
Node = Literal["D1", "D2", "D3", "D4", "D5", "D6", "N/A"]
Method = Literal["interview", "task_test"]

class ParticipantRecord(BaseModel):
    participant_id: str = Field(description="Unique identifier for the participant, e.g., P01")
    stage: Stage = Field(description="Journey stage or part of the interview")
    node: Node = Field(description="Decomposition node (first failing node if applicable)")
    code: str = Field(description="Thematic code or tag from the codebook")
    verbatim: str = Field(description="Exact quote or observation from the participant")
    method: Method = Field(description="Research method used")

class ResearchLedger:
    def __init__(self, records: list[ParticipantRecord] = None):
        self.records = records or []
        
    @classmethod
    def from_csv(cls, path: str):
        """Load the participant ledger from a CSV file."""
        df = pd.read_csv(path)
        records = [ParticipantRecord(**row) for row in df.to_dict('records')]
        return cls(records=records)
        
    def to_csv(self, path: str):
        """Export the participant ledger to a CSV file."""
        df = pd.DataFrame([r.model_dump() for r in self.records])
        df.to_csv(path, index=False)
