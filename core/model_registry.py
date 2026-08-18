"""Runtime model registry for NEXTRON X-100."""

from dataclasses import dataclass
from typing import Iterable


@dataclass
class ModelProfile:
    name: str
    provider: str
    coding: int = 0
    reasoning: int = 0
    vision: int = 0
    research: int = 0
    image_generation: int = 0
    reliability: int = 50
    speed: int = 50
    context: int = 0
    enabled: bool = True

    def capability(self, task_type: str) -> int:
        return getattr(self, task_type, 0)


class ModelRegistry:
    """Provider-independent collection of models available to the router."""

    def __init__(self, models: Iterable[ModelProfile] = ()) -> None:
        self._models: dict[str, ModelProfile] = {}
        for model in models:
            self.register(model)

    def register(self, model: ModelProfile) -> None:
        self._models[model.name] = model

    def get(self, name: str) -> ModelProfile | None:
        return self._models.get(name)

    def available(self) -> list[ModelProfile]:
        return [model for model in self._models.values() if model.enabled]

    def all(self) -> list[ModelProfile]:
        return list(self._models.values())

    def disable(self, name: str) -> None:
        model = self.get(name)
        if model is not None:
            model.enabled = False

    def enable(self, name: str) -> None:
        model = self.get(name)
        if model is not None:
            model.enabled = True
