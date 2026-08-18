"""NEXTRON X-100 runtime entry point."""

from __future__ import annotations

import os

from core.orchestrator import Orchestrator, registry_from_providers
from core.providers.openai_compatible import OpenAICompatibleProvider


def build_orchestrator() -> Orchestrator:
    """Build NEXTRON with the configured OpenRouter provider."""
    providers = {}
    if os.getenv("OPENROUTER_API_KEY"):
        providers["openrouter"] = OpenAICompatibleProvider(
            name="openrouter",
            base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
            api_key_env="OPENROUTER_API_KEY",
            capabilities={"coding": 90, "reasoning": 90, "research": 80},
            reliability=85,
            speed=80,
        )
    return Orchestrator(registry_from_providers(providers), providers)


if __name__ == "__main__":
    task = "Debug my Android Kotlin build"
    orchestrator = build_orchestrator()
    if not orchestrator.providers:
        print("No AI provider configured. Set OPENROUTER_API_KEY to enable OpenRouter.")
    else:
        result = orchestrator.execute(task)
        print(f"Task: {task}")
        print(f"Selected model: {result.model.name}")
        print(f"Provider: {result.provider}")
        print(f"Attempts: {result.attempts}")
        print("\nResponse:\n")
        print(result.text)
