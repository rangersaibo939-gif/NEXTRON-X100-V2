"""Lightweight task planner for NEXTRON.

Turns a user request into a small, ordered execution plan without requiring
an external model. A future LLM planner can replace this component while
keeping the same plan interface.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.router_engine import Router


@dataclass(frozen=True)
class PlanStep:
    name: str
    task: str
    task_type: str
    depends_on: tuple[str, ...] = ()


@dataclass(frozen=True)
class TaskPlan:
    goal: str
    steps: tuple[PlanStep, ...]


class Planner:
    def __init__(self, router: Router) -> None:
        self.router = router

    def plan(self, goal: str) -> TaskPlan:
        task_type = self.router.classify(goal)
        lower = goal.lower()

        if task_type == "research":
            steps = (
                PlanStep("research", goal, "research"),
                PlanStep("synthesize", f"Synthesize findings for: {goal}", "reasoning", ("research",)),
            )
        elif task_type == "coding" or any(x in lower for x in ("build", "fix", "implement")):
            steps = (
                PlanStep("analyze", f"Analyze requirements and constraints: {goal}", "reasoning"),
                PlanStep("implement", goal, "coding", ("analyze",)),
                PlanStep("review", f"Review the proposed implementation for: {goal}", "reasoning", ("implement",)),
            )
        else:
            steps = (PlanStep("solve", goal, task_type),)

        return TaskPlan(goal=goal, steps=steps)
