"""Strict observational output for optional remote scene assessment."""

from pydantic import Field

from neuravac_core.models import FloorClass, StrictModel


class HazardAssessment(StrictModel):
    class_name: FloorClass
    confidence: float = Field(ge=0, le=1)
    hazard_score: float = Field(ge=0, le=1)
    traversable: bool
    reason: str = Field(min_length=1, max_length=500)
