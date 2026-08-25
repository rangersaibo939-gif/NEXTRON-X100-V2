from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

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
    """Run specialist brains through providers selected by capability."""

    ROLE_CAPABILITIES = {
        "coder": "coding",
        "reasoner": "reasoning",
        "researcher": "research",
        "vision": "vision",
    }
    DEFAULT_ROLES = ("coder", "reasoner", "researcher")

    def __init__(self, providers: Mapping[str, AIProvider], max_workers: int = 4):
        self.providers = dict(providers)
        self.max_workers = max(1, max_workers)

    def _provider_for_role(self, role: str) -> AIProvider | None:
        capability = self.ROLE_CAPABILITIES[role]
        candidates = []
        for provider in self.providers.values():
            try:
                score = (getattr(provider, "capabilities", {}) or {}).get(capability, 0)
                available = provider.is_available()
            except Exception:
                continue
            if score and available:
                candidates.append((score, provider))
        return max(candidates, key=lambda item: item[0])[1] if candidates else None

    @staticmethod
    def _run(role: str, task: str, provider: AIProvider) -> BrainExecution:
        prompt = (
            f"You are the NEXTRON {role} brain.\n"
            "Solve the user's task from your specialist perspective. "
            "Be concrete and propose actionable steps.\n\n"
            f"USER TASK:\n{task}"
        )
        try:
            response = provider.generate(prompt)
        except Exception as exc:
            response = AIResponse(success=False, text="", provider=getattr(provider, "name", ""), model="", error=str(exc))
        return BrainExecution(role, response)

    def run(self, task: str, roles: Iterable[str] | None = None) -> MultiBrainResult:
        text = task.strip()
        if not text:
            raise ValueError("task must not be empty")
        selected = tuple(roles or self.DEFAULT_ROLES)
        for role in selected:
            if role not in self.ROLE_CAPABILITIES:
                raise ValueError(f"Unknown brain role: {role}")

        results = []
        for role in selected:
            provider = self._provider_for_role(role)
            if provider is None:
                response = AIResponse(success=False, text="", provider="", model="", error=f"No available provider for {role}")
                results.append(BrainExecution(role, response))
            else:
                results.append(self._run(role, text, provider))

        successful = [item.output.strip() for item in results if item.success and item.output.strip()]
        if not successful:
            raise RuntimeError("All NEXTRON brains failed")
        if len(successful) == 1:
            consensus = successful[0]
        else:
            judge = self._provider_for_role("reasoner") or self._provider_for_role("coder")
            if judge is None:
                consensus = "\n\n".join(successful)
            else:
                evidence = "\n\n".join(f"[{item.role.upper()} BRAIN]\n{item.output}" for item in results if item.success)
                prompt = (
                    "You are the NEXTRON lead judge. Synthesize the specialist outputs below.\n"
                    "Resolve contradictions, preserve useful details, and return one actionable answer.\n"
                    f"USER TASK:\n{text}\n\n{evidence}"
                )
                try:
                    verdict = judge.generate(prompt)
                except Exception:
                    verdict = None
                consensus = verdict.text.strip() if verdict and verdict.success and verdict.text.strip() else "\n\n".join(successful)

        return MultiBrainResult(tuple(results), consensus)


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
