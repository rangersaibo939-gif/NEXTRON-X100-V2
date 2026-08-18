"""NEXTRON X-100 runtime entry point."""

from __future__ import annotations

from core.orchestrator import Orchestrator, registry_from_providers
from core.providers.catalog import build_providers


def build_orchestrator() -> Orchestrator:
    """Build NEXTRON from the centralized provider catalog."""
    providers = build_providers()
    return Orchestrator(registry_from_providers(providers), providers)


if __name__ == "__main__":
    task = "Debug my Android Kotlin build"
    orchestrator = build_orchestrator()
    if not orchestrator.providers:
        print("No AI provider configured. Set a supported provider API key.")
    else:
        result = orchestrator.execute(task)
        print(f"Task: {task}")
        print(f"Selected model: {result.model.name}")
        print(f"Provider: {result.provider}")
        print(f"Attempts: {result.attempts}")
        print("\nResponse:\n")
        print(result.text)
