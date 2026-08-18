"""Provider-independent intelligent routing and failover."""

from dataclasses import dataclass
from typing import Callable

from core.model_registry import ModelProfile, ModelRegistry


@dataclass
class RouteDecision:
    task_type: str
    model: ModelProfile
    score: int


class Router:
    def __init__(self, registry: ModelRegistry) -> None:
        self.registry = registry
        self.failures: dict[str, int] = {}

    @staticmethod
    def classify(task: str) -> str:
        text = task.lower()
        if any(x in text for x in ("generate image", "create image", "draw")):
            return "image_generation"
        if any(x in text for x in ("image", "photo", "picture", "vision", "screenshot")):
            return "vision"
        if any(x in text for x in ("research", "latest", "search the web", "internet")):
            return "research"
        if any(x in text for x in ("code", "coding", "program", "python", "kotlin", "android", "bug", "debug", "compile")):
            return "coding"
        return "reasoning"

    def score(self, model: ModelProfile, task_type: str) -> int:
        failure_penalty = self.failures.get(model.name, 0) * 25
        return (
            model.capability(task_type) * 5
            + model.reliability * 2
            + model.speed
            - failure_penalty
        )

    def rank(self, task: str) -> list[RouteDecision]:
        task_type = self.classify(task)
        candidates = self.registry.available()
        ranked = [RouteDecision(task_type, model, self.score(model, task_type)) for model in candidates]
        return sorted(ranked, key=lambda item: item.score, reverse=True)

    def choose(self, task: str) -> RouteDecision | None:
        ranked = self.rank(task)
        return ranked[0] if ranked else None

    def execute_with_failover(
        self,
        task: str,
        executor: Callable[[ModelProfile, str], str],
    ) -> tuple[ModelProfile, str]:
        ranked = self.rank(task)
        if not ranked:
            raise RuntimeError("No enabled AI models are available")

        last_error: Exception | None = None
        for decision in ranked:
            model = decision.model
            try:
                result = executor(model, task)
                return model, result
            except Exception as exc:
                self.failures[model.name] = self.failures.get(model.name, 0) + 1
                last_error = exc

        raise RuntimeError("All candidate AI models failed") from last_error
