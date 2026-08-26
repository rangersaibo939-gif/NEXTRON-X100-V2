from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable, Mapping

from core.multi_brain import MultiBrainOrchestrator
from core.providers.base import AIProvider


DEFAULT_CAPABILITIES = (
    "multi-brain orchestration",
    "autonomous coding",
    "build monitoring",
    "APK delivery",
    "dashboard interaction",
    "keyboard-safe scrolling",
    "local build action",
)


@dataclass(frozen=True)
class DevelopmentTask:
    title: str
    capability: str
    description: str
    status: str = "queued"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass(frozen=True)
class SelfImprovementResult:
    capabilities: tuple[str, ...]
    missing_capabilities: tuple[str, ...]
    task: DevelopmentTask | None
    consensus: str = ""
    status: str = "idle"


class SelfImprovementLoop:
    """Turn capability gaps into concrete, multi-brain development tasks."""

    def __init__(self, providers: Mapping[str, AIProvider] | None = None, capabilities: Iterable[str] = ()):
        self.providers = dict(providers or {})
        self.capabilities = {item.strip().lower() for item in capabilities if item.strip()}
        self.history: list[DevelopmentTask] = []

    def inspect(self, required: Iterable[str] = DEFAULT_CAPABILITIES) -> tuple[str, ...]:
        required_set = tuple(dict.fromkeys(item.strip().lower() for item in required if item.strip()))
        return tuple(item for item in required_set if item not in self.capabilities)

    def create_task(self, capability: str, description: str | None = None) -> DevelopmentTask:
        name = capability.strip().lower()
        if not name:
            raise ValueError("capability must not be empty")
        task = DevelopmentTask(
            title=f"Implement {name}",
            capability=name,
            description=description or f"Add and verify NEXTRON capability: {name}.",
        )
        self.history.append(task)
        return task

    def plan_next(self, required: Iterable[str] = DEFAULT_CAPABILITIES) -> DevelopmentTask | None:
        missing = self.inspect(required)
        return self.create_task(missing[0]) if missing else None

    def run_agent(self, task: DevelopmentTask) -> SelfImprovementResult:
        if not self.providers:
            return SelfImprovementResult(tuple(sorted(self.capabilities)), self.inspect(), task, status="planned")
        result = MultiBrainOrchestrator(self.providers).run(
            f"{task.title}. {task.description}. Produce an implementation plan, coding approach, review checklist, and test strategy.",
            roles=("coder", "reasoner", "researcher"),
        )
        return SelfImprovementResult(
            tuple(sorted(self.capabilities)),
            self.inspect(),
            task,
            consensus=result.consensus,
            status="planned",
        )

    def snapshot(self) -> SelfImprovementResult:
        missing = self.inspect()
        task = self.history[-1] if self.history else None
        return SelfImprovementResult(tuple(sorted(self.capabilities)), missing, task, status="ready")
