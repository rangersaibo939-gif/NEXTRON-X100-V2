from core.model_registry import ModelProfile, ModelRegistry
from core.orchestrator import Orchestrator
from core.providers.base import AIProvider, AIResponse


class FakeProvider(AIProvider):
    def __init__(self, name: str, fail: bool = False):
        self.name = name
        self.fail = fail
        self.calls = 0

    def is_available(self) -> bool:
        return True

    def generate(self, prompt: str) -> AIResponse:
        self.calls += 1
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
