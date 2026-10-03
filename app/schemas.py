"""Single source of truth for all Pydantic models."""
from typing import Literal

from pydantic import BaseModel, Field

Dimension = Literal["accuracy", "logic", "completeness"]

Category = Literal[
    "fabricated_fact", "wrong_number", "wrong_date", "misattribution", "outdated_claim",
    "non_sequitur", "unsupported_conclusion", "logical_fallacy", "internal_contradiction",
    "missing_subquestion", "off_topic", "insufficient_depth", "other",
]


class Issue(BaseModel):
    quote: str = Field(description="Exact substring copied from the original output")
    problem: str
    severity: int = Field(ge=1, le=5)
    category: Category


class Critique(BaseModel):
    dimension: Dimension
    # reasoning before score nudges chain-of-thought into the structured output
    reasoning_summary: str
    issues: list[Issue] = []
    validated_claims: list[str] = []   # drives green markers in the UI
    score: int = Field(ge=1, le=5)
    confidence: float = Field(ge=0, le=1)


class CriticFailure(BaseModel):
    dimension: Dimension
    error: str
    attempts: int


class Disagreement(BaseModel):
    type: Literal["severity_gap", "flag_vs_validated", "unique_finding", "score_spread"]
    critics: list[Dimension]
    quotes: list[str] = []
    summary: str


class Resolution(BaseModel):
    disagreement_summary: str
    reasoning: str
    outcome: str
    evidence: list[str] = []


class ConfirmedIssue(BaseModel):
    quote: str
    problem: str
    severity: int = Field(ge=1, le=5)
    raised_by: list[Dimension]
    evidence: str


class DismissedFlag(BaseModel):
    quote: str
    raised_by: Dimension
    original_problem: str
    dismissal_reasoning: str


class Verdict(BaseModel):
    disagreement_resolutions: list[Resolution] = []
    confirmed_issues: list[ConfirmedIssue] = []
    dismissed_flags: list[DismissedFlag] = []
    validated_claims: list[str] = []
    summary: str
    overall_score: int = Field(ge=1, le=10)
    confidence: float = Field(ge=0, le=1)
    degraded: bool = False
    missing_dimensions: list[Dimension] = []


# ---- API models ----
class ArbitrateRequest(BaseModel):
    output: str = Field(min_length=1)
    prompt: str | None = None


class ArbitrateResponse(BaseModel):
    arbitration_id: str
    verdict: Verdict
    critiques: list[Critique]
    disagreements: list[Disagreement]
    latency_ms: int
