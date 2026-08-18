from core.providers.base import AIProvider, AIResponse


class TestProvider(AIProvider):
    def generate(self, prompt: str) -> AIResponse:
        return AIResponse(
            text=f"Test response for: {prompt}",
            model="test-model",
            provider="test",
        )


def test_provider_interface():
    provider = TestProvider()

    response = provider.generate("Hello NEXTRON")

    assert response.success is True
    assert response.model == "test-model"
    assert response.provider == "test"
    assert "Hello NEXTRON" in response.text


def test_provider_availability():
    provider = TestProvider()

    assert provider.is_available() is True
