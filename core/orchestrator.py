"""End-to-end NEXTRON orchestration engine.

The orchestrator connects the model registry, router, and provider layer.
It deliberately keeps provider credentials out of source control.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from core.model_registry import ModelProfile, ModelRegistry
from core.router_engine import Router
from core.providers.base import AIProvider, AIResponse


@dataclass
class ExecutionResult:
    text: str
    model: ModelProfile
    provider: str
    task_type: str
    attempts: int


class Orchestrator:
    """Route a task to the best model and execute it with failover."""

    def __init__(
        self,
        registry: ModelRegistry,
        providers: dict[str, AIProvider],
    ) -> None:
        self.registry = registry
        self.providers = providers
        self.router = Router(registry)

    def execute(self, task: str) -> ExecutionResult:
        decisions = self.router.rank(task)
        if not decisions:
            raise RuntimeError("No enabled AI models are available")

        last_error: str | None = None
        attempts = 0

        for decision in decisions:
            model = decision.model
            provider = self.providers.get(model.provider)
            if provider is None or not provider.is_available():
                self.router.failures[model.name] = self.router.failures.get(model.name, 0) + 1
                last_error = f"Provider unavailable: {model.provider}"
                continue

            attempts += 1
            response = provider.generate(task)
            if response.success and response.text.strip():
                return ExecutionResult(
                    text=response.text,
                    model=model,
                    provider=response.provider,
                    task_type=decision.task_type,
                    attempts=attempts,
                )

            self.router.failures[model.name] = self.router.failures.get(model.name, 0) + 1
            last_error = response.error or "Provider returned an empty response"

        raise RuntimeError(f"All candidate AI models failed: {last_error}")


def registry_from_providers(providers: dict[str, AIProvider]) -> ModelRegistry:
    """Build a minimal registry from provider objects that expose model metadata.

    Providers may optionally expose a ``model_profile`` attribute. This keeps
    provider-specific metadata out of the router while allowing dynamic setup.
    """
    registry = ModelRegistry()
    for provider in providers.values():
        profile = getattr(provider, "model_profile", None)
        if isinstance(profile, ModelProfile):
            registry.register(profile)
    return registry
