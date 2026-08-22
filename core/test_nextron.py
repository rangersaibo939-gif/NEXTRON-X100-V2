from core.model_registry import ModelProfile, ModelRegistry
from core.router_engine import Router, classify_task


def make_router() -> Router:
    registry = ModelRegistry(
        [
            ModelProfile("Coding Specialist", "test", coding=95, reasoning=80, reliability=90, speed=80),
            ModelProfile("Research Specialist", "test", research=95, reasoning=90, reliability=92, speed=75),
        ]
    )
    return Router(registry)


def test_task_classification():
    assert classify_task("Debug my Android Kotlin build") == "coding"
    assert classify_task("Research the latest AI models") == "research"


def test_model_selection():
    router = make_router()
    decision = router.choose("Debug my Android Kotlin build")

    assert decision is not None
    assert decision.model.name == "Coding Specialist"