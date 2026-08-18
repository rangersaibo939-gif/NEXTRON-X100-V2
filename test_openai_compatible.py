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
