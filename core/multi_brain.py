from __future__ import annotations

from dataclasses import dataclass

from core.providers.base import AIProvider, AIResponse


@dataclass(frozen=True)
class BrainExecution:
    role: str
    response: AIResponse

    @property
    def success(self) -> bool:
        return self.response.success

    @property
    def output(self) -> str:
        return self.response.text


@dataclass(frozen=True)
class MultiBrainResult:
    results: tuple[BrainExecution, ...]
    consensus: str


class MultiBrainOrchestrator:
    """Run a multi-brain workflow through injected providers."""

    DEFAULT_ROLES = ("coder", "reasoner", "researcher")

    def __init__(self, providers: dict[str, AIProvider]):
        self.providers = dict(providers)

    def run(self, task: str, roles: list[str] | tuple[str, ...] | None = None) -> MultiBrainResult:
        text = task.strip()
        if not text:
            raise ValueError("task must not be empty")

        selected = tuple(roles or self.DEFAULT_ROLES)
        for role in selected:
            if role not in self.providers:
                raise ValueError(f"Unknown brain role: {role}")

        results = tuple(
            BrainExecution(role, self.providers[role].generate(self._role_prompt(role, text)))
            for role in selected
        )
        successful = [item.output for item in results if item.success]
        if not successful:
            return MultiBrainResult(results, "")
        if len(successful) == 1:
            return MultiBrainResult(results, successful[0])

        judge = self.providers.get("reasoner")
        if judge is None:
            consensus = "\n\n".join(successful)
        else:
            evidence = "\n\n".join(f"[{item.role}] {item.output}" for item in results if item.success)
            verdict = judge.generate(
                f"Act as the judge for this task:\n{text}\n\n"
                f"Review these specialist outputs and return the best consensus:\n{evidence}"
            )
            consensus = verdict.text if verdict.success else "\n\n".join(successful)
        return MultiBrainResult(results, consensus)

    @staticmethod
    def _role_prompt(role: str, task: str) -> str:
        instructions = {
            "coder": "Focus on implementation, testability, and the smallest working solution.",
            "reasoner": "Focus on architecture, constraints, risks, and a coherent solution.",
            "researcher": "Focus on evidence, requirements, alternatives, and practical dependencies.",
        }
        return f"{instructions.get(role, 'Analyze the task carefully.')}\n\nTask: {task}"


@dataclass(frozen=True)
class BrainResult:
    role: str
    output: str


class MultiBrain:
    """Compatibility facade used by the generated app."""

    def run(self, request: str) -> tuple[BrainResult, ...]:
        text = request.strip()
        if not text:
            raise ValueError("request must not be empty")
        return (
            BrainResult("planner", f"Plan: define the Android app structure and user flow for: {text}"),
            BrainResult("coder", "Coder: generate the smallest testable Android implementation from the plan."),
            BrainResult("reviewer", "Reviewer: validate the plan, implementation scope, and build readiness."),
        )
