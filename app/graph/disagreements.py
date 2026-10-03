"""Deterministic, LLM-free disagreement detector. Rules:
 1. severity_gap      - overlapping quotes, severities differ by > 2
 2. flag_vs_validated - one critic flags text another validated
 3. unique_finding    - cross-dimension only (not a critic's own mandate)
 4. score_spread      - dimension scores differ by >= 2
"""
from app.schemas import Critique, Disagreement


def detect_disagreements(critiques: list[Critique], source: str) -> list[Disagreement]:
    out: list[Disagreement] = []
    scores = {c.dimension: c.score for c in critiques}
    if scores and max(scores.values()) - min(scores.values()) >= 2:
        out.append(Disagreement(type="score_spread", critics=list(scores),
                                summary=f"Scores spread: {scores}"))
    # TODO: implement span-overlap helpers + rules 1-3
    return out
