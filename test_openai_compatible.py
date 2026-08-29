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


def test_chat_endpoint_accepts_base_url():
    provider = OpenAICompatibleProvider(
        name="groq",
        base_url="https://api.groq.com/openai/v1",
        model="openai/gpt-oss-20b",
        api_key_env="TEST_NEXTRON_KEY",
    )
    assert provider.chat_completions_url == "https://api.groq.com/openai/v1/chat/completions"


def test_chat_endpoint_does_not_double_append_chat_completions():
    provider = OpenAICompatibleProvider(
        name="groq",
        base_url="https://api.groq.com/openai/v1/chat/completions",
        model="openai/gpt-oss-20b",
        api_key_env="TEST_NEXTRON_KEY",
    )
    assert provider.chat_completions_url == "https://api.groq.com/openai/v1/chat/completions"
