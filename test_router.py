from core.model_registry import ModelProfile, ModelRegistry
from core.router_engine import Router


def make_router() -> Router:
    registry = ModelRegistry(
        [
            ModelProfile("Coding AI", "test", coding=95, reasoning=80, reliability=90, speed=80),
            ModelProfile("Research AI", "test", research=95, reasoning=90, reliability=92, speed=75),
            ModelProfile("Vision AI", "test", vision=95, reliability=88, speed=70),
        ]
    )
    return Router(registry)


def test_router_selects_specialist():
    router = make_router()
    decision = router.choose("Debug my Android Kotlin build")
    assert decision is not None
    assert decision.model.name == "Coding AI"


def test_router_selects_research_model():
    router = make_router()
    decision = router.choose("Research the latest AI models")
    assert decision is not None
    assert decision.model.name == "Research AI"


def test_failover_moves_to_next_model():
    router = make_router()
    calls = []

    def executor(model, task):
        calls.append(model.name)
        if model.name == "Coding AI":
            raise RuntimeError("temporary provider failure")
        return "success"

    model, result = router.execute_with_failover("Debug Python code", executor)

    assert result == "success"
    assert model.name == "Research AI" or model.name == "Vision AI"
    assert calls[0] == "Coding AI"


def test_disabled_model_is_not_selected():
    router = make_router()
    router.registry.disable("Coding AI")
    decision = router.choose("Debug my Android build")
    assert decision is not None
    assert decision.model.name != "Coding AI"
