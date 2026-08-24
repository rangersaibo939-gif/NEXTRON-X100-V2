from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Iterable, Mapping

from core.providers.base import AIProvider, AIResponse


@dataclass(frozen=True)
class BrainResult:
    role: str
    provider: str
    model: str
    text: str
    success: bool
    error: str | None = None


@dataclass(frozen=True)
class MultiBrainResult:
    task: str
    results: tuple[BrainResult, ...]
    consensus: str


class MultiBrainOrchestrator:
    """Run specialist AI brains concurrently and synthesize their outputs."""

    ROLE_CAPABILITIES = {
        "coder": "coding",
        "reasoner": "reasoning",
        "researcher": "research",
        "vision": "vision",
    }

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
    def _run(role: str, task: str, provider: AIProvider) -> BrainResult:
        prompt = (
            f"You are the NEXTRON {role} brain.\n"
            "Solve the user's task from your specialist perspective. "
            "Be concrete, identify assumptions, and propose actionable steps.\n\n"
            f"USER TASK:\n{task}"
        )
        try:
            response: AIResponse = provider.generate(prompt)
        except Exception as exc:
            return BrainResult(role, getattr(provider, "name", ""), "", "", False, str(exc))
        if not response.success or not response.text.strip():
            return BrainResult(role, response.provider, response.model, "", False, response.error or "empty response")
        return BrainResult(role, response.provider, response.model, response.text.strip(), True)

    def run(self, task: str, roles: Iterable[str] | None = None) -> MultiBrainResult:
        task = task.strip()
        if not task:
            raise ValueError("task must not be empty")
        selected = list(roles or ("coder", "reasoner", "researcher"))
        for role in selected:
            if role not in self.ROLE_CAPABILITIES:
                raise ValueError(f"Unknown brain role: {role}")

        results: list[BrainResult] = []
        with ThreadPoolExecutor(max_workers=min(self.max_workers, len(selected) or 1)) as pool:
            futures = {}
            for role in selected:
                provider = self._provider_for_role(role)
                if provider is None:
                    results.append(BrainResult(role, "", "", "", False, f"No available provider for {role}"))
                else:
                    futures[pool.submit(self._run, role, task, provider)] = role
            for future in as_completed(futures):
                results.append(future.result())

        order = {role: i for i, role in enumerate(selected)}
        results.sort(key=lambda result: order[result.role])
        successful = [result for result in results if result.success and result.text]
        if not successful:
            errors = "; ".join(f"{r.role}: {r.error}" for r in results)
            raise RuntimeError(f"All NEXTRON brains failed: {errors}")

        if len(successful) == 1:
            consensus = successful[0].text
        else:
            prompt = [
                "You are the NEXTRON lead judge. Synthesize the specialist outputs below.",
                "Resolve contradictions, preserve useful details, and return one actionable answer.",
                "Do not mention the internal brain process.",
                f"USER TASK:\n{task}\n",
            ]
            prompt.extend(f"[{r.role.upper()} BRAIN]\n{r.text}\n" for r in successful)
            judge = self._provider_for_role("reasoner") or self._provider_for_role("coder")
            if judge is None:
                consensus = "\n\n".join(r.text for r in successful)
            else:
                try:
                    response = judge.generate("\n".join(prompt))
                except Exception:
                    response = None
                if response is not None and response.success and response.text.strip():
                    consensus = response.text.strip()
                else:
                    # A judge/provider failure must not discard successful specialist work.
                    consensus = "\n\n".join(r.text for r in successful)

        return MultiBrainResult(task, tuple(results), consensus)
