import json
from urllib.error import HTTPError
from urllib.request import Request

from core.providers.openai_compatible import OpenAICompatibleProvider


class _FakeResponse:
    def __init__(self, body):
        self.body = json.dumps(body).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.body


def _provider(api_key_env):
    return OpenAICompatibleProvider(
        name="test",
        base_url="https://example.invalid/v1",
        model="test-model",
        api_key_env=api_key_env,
    )


def test_provider_without_key_is_unavailable(monkeypatch):
    monkeypatch.delenv("TEST_NEXTRON_KEY", raising=False)
    provider = _provider("TEST_NEXTRON_KEY")
    assert provider.is_available() is False


def test_provider_reads_single_key_from_environment(monkeypatch):
    monkeypatch.setenv("TEST_NEXTRON_KEY", "test-only")
    provider = _provider("TEST_NEXTRON_KEY")
    assert provider.is_available() is True


def test_multiple_keys_fall_back_after_auth_failure(monkeypatch):
    monkeypatch.setenv("TEST_NEXTRON_KEY_1", "secret-one")
    monkeypatch.setenv("TEST_NEXTRON_KEY_2", "secret-two")
    provider = _provider(["TEST_NEXTRON_KEY_1", "TEST_NEXTRON_KEY_2"])
    calls = []

    def fake_urlopen(req: Request, timeout):
        calls.append(req.get_header("Authorization"))
        if len(calls) == 1:
            raise HTTPError(req.full_url, 401, "unauthorized", {}, None)
        return _FakeResponse({"choices": [{"message": {"content": "ok"}}]})

    monkeypatch.setattr("core.providers.openai_compatible.request.urlopen", fake_urlopen)
    result = provider.generate("hello")

    assert result.success is True
    assert result.text == "ok"
    assert calls == ["Bearer secret-one", "Bearer secret-two"]


def test_non_retryable_http_failure_does_not_rotate(monkeypatch):
    monkeypatch.setenv("TEST_NEXTRON_KEY_1", "secret-one")
    monkeypatch.setenv("TEST_NEXTRON_KEY_2", "secret-two")
    provider = _provider(["TEST_NEXTRON_KEY_1", "TEST_NEXTRON_KEY_2"])
    calls = []

    def fake_urlopen(req: Request, timeout):
        calls.append(req.get_header("Authorization"))
        raise HTTPError(req.full_url, 400, "bad request", {}, None)

    monkeypatch.setattr("core.providers.openai_compatible.request.urlopen", fake_urlopen)
    result = provider.generate("hello")

    assert result.success is False
    assert result.error == "Provider request failed"
    assert calls == ["Bearer secret-one"]


def test_exhausted_keys_redact_provider_error(monkeypatch):
    monkeypatch.setenv("TEST_NEXTRON_KEY_1", "super-secret-one")
    monkeypatch.setenv("TEST_NEXTRON_KEY_2", "super-secret-two")
    provider = _provider(["TEST_NEXTRON_KEY_1", "TEST_NEXTRON_KEY_2"])

    def fake_urlopen(req: Request, timeout):
        raise HTTPError(req.full_url, 429, "rate limited", {}, None)

    monkeypatch.setattr("core.providers.openai_compatible.request.urlopen", fake_urlopen)
    result = provider.generate("hello")

    assert result.success is False
    assert result.error == "Provider request failed"
    assert "super-secret" not in result.error
