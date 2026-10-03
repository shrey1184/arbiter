from app.graph.build import route_after_detect
from app.schemas import Critique


def test_clean_pass_short_circuits():
    cs = [Critique(dimension=d, reasoning_summary="ok", score=5, confidence=0.9)
          for d in ("accuracy", "logic", "completeness")]
    assert route_after_detect({"critiques": cs, "failures": []}) == "short_circuit"


# TODO: mocked-LLM tests: happy path, one critic failing (degraded), all failing, parallel timing
