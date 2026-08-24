from core.multi_brain import MultiBrainOrchestrator
from core.providers.base import AIProvider, AIResponse


class FakeProvider(AIProvider):
    def __init__(self, name: str, text: str, capabilities: dict[str, int]):
        self.name = name
        self.text = text
        self.capabilities = capabilities
        self.calls: list[str] = []

    def generate(self, prompt: str) -> AIResponse:
        self.calls.append(prompt)
        return AIResponse(self.text, "fake-model", self.name)


def test_routes_specialists_and_judge():
    coder = FakeProvider("coder", "implementation", {"coding": 95})
    reasoner = FakeProvider("reasoner", "architecture", {"reasoning": 96})
    researcher = FakeProvider("researcher", "evidence", {"research": 94})
    result = MultiBrainOrchestrator({"coder": coder, "reasoner": reasoner, "researcher": researcher}).run("Build a reliable app")
    assert [r.role for r in result.results] == ["coder", "reasoner", "researcher"]
    assert all(r.success for r in result.results)
    assert result.consensus
    assert len(reasoner.calls) == 2


def test_unknown_role_rejected():
    provider = FakeProvider("p", "ok", {"coding": 90})
    try:
        MultiBrainOrchestrator({"p": provider}).run("task", roles=["unknown"])
    except ValueError as exc:
        assert "Unknown brain role" in str(exc)
    else:
        raise AssertionError("unknown role should fail")


def test_single_brain_uses_one_call():
    provider = FakeProvider("coder", "answer", {"coding": 90})
    result = MultiBrainOrchestrator({"coder": provider}).run("task", roles=["coder"])
    assert result.consensus == "answer"
    assert len(provider.calls) == 1
