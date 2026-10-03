from app.graph.disagreements import detect_disagreements
from app.schemas import Critique


def _c(dim, score):
    return Critique(dimension=dim, reasoning_summary="x", score=score, confidence=0.9)


def test_score_spread_flagged():
    out = detect_disagreements([_c("accuracy", 5), _c("logic", 2), _c("completeness", 4)], "text")
    assert any(d.type == "score_spread" for d in out)


def test_no_spread_no_flag():
    out = detect_disagreements([_c("accuracy", 4), _c("logic", 4), _c("completeness", 5)], "text")
    assert out == []
