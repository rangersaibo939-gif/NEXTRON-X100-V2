from core.providers.openai_compatible import OpenAICompatibleProvider


def test_provider_without_key_is_unavailable(monkeypatch):
    monkeypatch.delenv("TEST_NEXTRON_KEY", raising=False)
    provider = OpenAICompatibleProvider(
        name="test",
        base_url="https://example.invalid/v1",
        model="test-model",
        api_key_env="TEST_NEXTRON_KEY",
    )
    assert provider.is_available() is False


def test_provider_reads_key_from_environment(monkeypatch):
    monkeypatch.setenv("TEST_NEXTRON_KEY", "test-only")
    provider = OpenAICompatibleProvider(
        name="test",
        base_url="https://example.invalid/v1",
        model="test-model",
        api_key_env="TEST_NEXTRON_KEY",
    )
    assert provider.is_available() is True


def test_provider_retries_429_then_succeeds(monkeypatch):
    monkeypatch.setenv("TEST_NEXTRON_KEY", "test-only")

    class FakeResponse:
        def __init__(self, status_code, payload=None):
            self.status_code = status_code
            self.headers = {}
            self._payload = payload or {}

        def raise_for_status(self):
            if self.status_code >= 400:
                raise RuntimeError(f"HTTP {self.status_code}")

        def json(self):
            return self._payload

    responses = [
        FakeResponse(429),
        FakeResponse(
            200,
            {"choices": [{"message": {"content": "NEXTRON RETRY PASSED"}}]},
        ),
    ]
    calls = []
    monkeypatch.setattr(
        "core.providers.openai_compatible.requests.post",
        lambda *args, **kwargs: calls.append(1) or responses.pop(0),
    )
    monkeypatch.setattr("core.providers.openai_compatible.time.sleep", lambda _: None)

    provider = OpenAICompatibleProvider(
        name="test",
        base_url="https://example.invalid/v1",
        model="test-model",
        api_key_env="TEST_NEXTRON_KEY",
        max_retries=2,
    )

    result = provider.generate("hello")

    assert result.success is True
    assert result.text == "NEXTRON RETRY PASSED"
    assert len(calls) == 2
