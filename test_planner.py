from core.model_registry import ModelProfile, ModelRegistry
from core.planner import Planner
from core.router_engine import Router


def planner() -> Planner:
    registry = ModelRegistry([
        ModelProfile(name="test", provider="test", coding=90, reasoning=90, research=90)
    ])
    return Planner(Router(registry))


def test_research_plan_has_synthesis_step():
    plan = planner().plan("Research the latest Android AI tools")
    assert [step.name for step in plan.steps] == ["research", "synthesize"]
    assert plan.steps[1].depends_on == ("research",)


def test_coding_plan_has_review_step():
    plan = planner().plan("Fix the Kotlin build failure")
    assert [step.name for step in plan.steps] == ["analyze", "implement", "review"]
    assert plan.steps[-1].depends_on == ("implement",)
