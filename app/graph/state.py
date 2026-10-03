import operator
from typing import Annotated, TypedDict

from app.schemas import Critique, CriticFailure, Disagreement, Verdict


class ArbState(TypedDict, total=False):
    arbitration_id: str
    original_prompt: str | None
    output_text: str
    critiques: Annotated[list[Critique], operator.add]     # reducer enables parallel writes
    failures: Annotated[list[CriticFailure], operator.add]
    disagreements: list[Disagreement]
    verdict: Verdict | None
