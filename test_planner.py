from core.model_registry import ModelProfile, ModelRegistry
from core.planner import Planner
from core.router_engine import Router


def planner() -> Planner:
    registry = ModelRegistry([
        ModelProfile(name="test", provider="test", coding=90, reasoning=90, research=90)
    ])
    return Planner(Router(registry))


def test_research_plan_is_multi_step():
    plan = planner().plan("Research the latest Android AI tools")
    assert [step.name for step in plan.steps] == [
        "research", "analyze", "verify", "synthesize"
    ]
    assert plan.steps[1].depends_on == ("research",)
    assert plan.steps[2].depends_on == ("analyze",)
    assert plan.steps[3].depends_on == ("verify",)


def test_coding_plan_is_multi_step():
    plan = planner().plan("Fix the Kotlin build failure")
    assert [step.name for step in plan.steps] == [
        "analyze", "implement", "test", "review", "synthesize"
    ]
    assert plan.steps[2].depends_on == ("implement",)
    assert plan.steps[3].depends_on == ("test",)
    assert plan.steps[4].depends_on == ("review",)


def test_complex_reasoning_plan_has_review_and_synthesis():
    plan = planner().plan(
        "Analyze how NEXTRON should improve its AI task routing, then give a concise recommendation."
    )
    assert [step.name for step in plan.steps] == ["analyze", "review", "synthesize"]
    assert plan.steps[1].depends_on == ("analyze",)
    assert plan.steps[2].depends_on == ("review",)
