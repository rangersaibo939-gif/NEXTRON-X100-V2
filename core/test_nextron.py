from core.model_registry import ModelProfile, ModelRegistry
from core.router_engine import Router


def build_registry():
    return ModelRegistry(
        [
            ModelProfile(
                name="Coding Specialist",
                provider="test",
                coding=95,
                reasoning=80,
                reliability=90,
                speed=80,
            ),
            ModelProfile(
                name="Research Specialist",
                provider="test",
                research=95,
                reasoning=90,
                reliability=92,
                speed=75,
            ),
        ]
    )


def test_task_classification():
    assert Router.classify("Debug my Android Kotlin build") == "coding"
    assert Router.classify("Research the latest AI models") == "research"


def test_model_selection():
    selected = Router(build_registry()).choose("Debug my Android Kotlin build")

    assert selected is not None
    assert selected.model.name == "Coding Specialist"
