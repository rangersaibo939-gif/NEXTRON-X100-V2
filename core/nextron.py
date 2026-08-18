"""
NEXTRON X-100
Multi-AI orchestration brain.

Phase 1:
- Task classification
- Model registry
- Capability matching
- Intelligent model selection
"""

from dataclasses import dataclass
from typing import List


@dataclass
class AIModel:
    name: str
    provider: str
    coding: int = 0
    reasoning: int = 0
    vision: int = 0
    research: int = 0
    image_generation: int = 0
    reliability: int = 0
    speed: int = 0


MODELS: List[AIModel] = []


def register_model(model: AIModel) -> None:
    """Add an AI model to the NEXTRON registry."""
    MODELS.append(model)


def classify_task(task: str) -> str:
    """Basic Phase-1 task classifier."""
    text = task.lower()

    if any(word in text for word in [
        "code", "coding", "program", "python", "kotlin",
        "java", "android", "bug", "debug", "compile"
    ]):
        return "coding"

    if any(word in text for word in [
        "image", "photo", "picture", "visual"
    ]):
        return "vision"

    if any(word in text for word in [
        "generate image", "create image", "draw"
    ]):
        return "image_generation"

    if any(word in text for word in [
        "research", "latest", "search", "internet", "find information"
    ]):
        return "research"

    return "reasoning"


def score_model(model: AIModel, task_type: str) -> int:
    """Score a model against the detected task."""
    capability = getattr(model, task_type, 0)

    return (
        capability * 5
        + model.reliability * 2
        + model.speed
    )


def choose_model(task: str) -> AIModel | None:
    """Select the highest-scoring available model."""
    task_type = classify_task(task)

    if not MODELS:
        return None

    return max(
        MODELS,
        key=lambda model: score_model(model, task_type)
    )


if __name__ == "__main__":
    register_model(
        AIModel(
            name="Example Coding AI",
            provider="example",
            coding=95,
            reasoning=85,
            reliability=90,
            speed=80,
        )
    )

    register_model(
        AIModel(
            name="Example Research AI",
            provider="example",
            research=95,
            reasoning=90,
            reliability=92,
            speed=75,
        )
    )

    task = "Debug my Android Kotlin build"

    selected = choose_model(task)

    if selected:
        print(f"Task: {task}")
        print(f"Selected model: {selected.name}")
        print(f"Provider: {selected.provider}")
    else:
        print("No AI models are registered.")