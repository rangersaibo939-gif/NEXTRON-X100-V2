from core.model_registry import ModelProfile, ModelRegistry
from core.orchestrator import Orchestrator
from core.providers.base import AIProvider, AIResponse


class FakeProvider(AIProvider):
    def __init__(self, name: str, fail: bool = False, raise_error: bool = False):
        self.name = name
        self.fail = fail
        self.raise_error = raise_error
        self.calls = 0

    def is_available(self) -> bool:
        return True

    def generate(self, prompt: str) -> AIResponse:
        self.calls += 1
        if self.raise_error:
            raise RuntimeError("simulated provider crash")
        if self.fail:
            return AIResponse("", "fake-model", self.name, False, "simulated failure")
        return AIResponse(f"handled: {prompt}", "fake-model", self.name)


def test_orchestrator_selects_best_provider():
    fast = FakeProvider("fast")
    slow = FakeProvider("slow")
    registry = ModelRegistry([
        ModelProfile("fast-model", "fast", coding=95, reliability=90, speed=95),
        ModelProfile("slow-model", "slow", coding=70, reliability=90, speed=50),
    ])

    result = Orchestrator(registry, {"fast": fast, "slow": slow}).execute("debug Kotlin code")

    assert result.model.name == "fast-model"
    assert result.provider == "fast"
    assert result.attempts == 1
    assert fast.calls == 1
    assert slow.calls == 0


def test_orchestrator_fails_over_to_second_model():
    first = FakeProvider("first", fail=True)
    second = FakeProvider("second")
    registry = ModelRegistry([
        ModelProfile("first-model", "first", coding=100, reliability=95, speed=95),
        ModelProfile("second-model", "second", coding=90, reliability=90, speed=90),
    ])

    result = Orchestrator(registry, {"first": first, "second": second}).execute("fix Android build")

    assert result.model.name == "second-model"
    assert result.provider == "second"
    assert result.attempts == 2
    assert first.calls == 1
    assert second.calls == 1


def test_orchestrator_fails_over_after_provider_exception():
    first = FakeProvider("first", raise_error=True)
    second = FakeProvider("second")
    registry = ModelRegistry([
        ModelProfile("first-model", "first", coding=100, reliability=95, speed=95),
        ModelProfile("second-model", "second", coding=90, reliability=90, speed=90),
    ])

    result = Orchestrator(registry, {"first": first, "second": second}).execute("continue task")

    assert result.provider == "second"
    assert result.attempts == 2


def test_orchestrator_rejects_empty_task():
    provider = FakeProvider("provider")
    registry = ModelRegistry([
        ModelProfile("model", "provider", coding=90, reliability=90, speed=90),
    ])

    try:
        Orchestrator(registry, {"provider": provider}).execute("   ")
    except ValueError as exc:
        assert str(exc) == "Task must not be empty"
    else:
        raise AssertionError("empty tasks must be rejected")
