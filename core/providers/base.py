from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class AIResponse:
    text: str
    model: str
    provider: str
    success: bool = True
    error: str | None = None


class AIProvider(ABC):
    """Common interface for every NEXTRON AI provider."""

    @abstractmethod
    def generate(self, prompt: str) -> AIResponse:
        """Generate a response from the provider."""
        raise NotImplementedError

    def is_available(self) -> bool:
        """Return whether the provider is currently available."""
        return True