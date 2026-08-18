from core.evaluator import ResultEvaluator


def test_evaluator_accepts_normal_response():
    result = ResultEvaluator().evaluate("A useful response")
    assert result.accepted is True
    assert result.score == 100


def test_evaluator_rejects_empty_response():
    result = ResultEvaluator().evaluate("  ")
    assert result.accepted is False
    assert "empty response" in result.reasons
