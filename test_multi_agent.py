from core.evaluator import ResultEvaluator
from core.model_registry import ModelProfile, ModelRegistry
from core.multi_agent import MultiAgentExecutor
from core.orchestrator import Orchestrator
from core.planner import PlanStep, TaskPlan
from core.providers.base import AIProvider, AIResponse


class FakeProvider(AIProvider):
    def __init__(self, name: str):
        self.name = name
        self.calls: list[str] = []

    def generate(self, prompt: str) -> AIResponse:
        self.calls.append(prompt)
        return AIResponse(f"result from {self.name}: {prompt}", "model", self.name)


def make_engine() -> tuple[MultiAgentExecutor, dict[str, FakeProvider]]:
    provider = FakeProvider("coding")
    registry = ModelRegistry([
        ModelProfile("coding-model", "coding", coding=100, reasoning=90, reliability=95, speed=90),
    ])
    orchestrator = Orchestrator(registry, {"coding": provider})
    return MultiAgentExecutor(orchestrator, ResultEvaluator()), {"coding": provider}


def test_executes_steps_in_order_and_passes_context():
    engine, providers = make_engine()
    plan = TaskPlan(
        "build feature",
        (
            PlanStep("analyze", "analyze requirements", "reasoning"),
            PlanStep("implement", "implement feature", "coding", ("analyze",)),
            PlanStep("review", "review feature", "reasoning", ("implement",)),
        ),
    )

    result = engine.execute(plan)

    assert [item.step.name for item in result.steps] == ["analyze", "implement", "review"]
    assert result.final_text == result.steps[-1].execution.text
    assert len(providers["coding"].calls) == 3
    assert "analyze" in providers["coding"].calls[1]
    assert "implement" in providers["coding"].calls[2]


def test_uses_synthesis_as_final_result():
    engine, _ = make_engine()
    plan = TaskPlan(
        "research",
        (
            PlanStep("research", "find facts", "research"),
            PlanStep("synthesize", "combine findings", "reasoning", ("research",)),
        ),
    )

    result = engine.execute(plan)

    assert result.steps[-1].step.name == "synthesize"
    assert result.final_text == result.steps[-1].execution.text


def test_rejects_unmet_dependency():
    engine, _ = make_engine()
    plan = TaskPlan(
        "bad plan",
        (PlanStep("review", "review", "reasoning", ("missing",)),),
    )

    try:
        engine.execute(plan)
    except RuntimeError as exc:
        assert "unmet dependencies" in str(exc)
    else:
        raise AssertionError("unmet dependencies must fail")
