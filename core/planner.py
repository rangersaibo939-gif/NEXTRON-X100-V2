"""Lightweight task planner for NEXTRON.

Turns a user request into a small, ordered execution plan without requiring
an external model. The planner deliberately keeps planning deterministic so
plans are reproducible; an LLM planner can replace this component later while
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
                PlanStep(
                    "analyze",
                    f"Analyze the research findings and identify the strongest evidence for: {goal}",
                    "reasoning",
                    ("research",),
                ),
                PlanStep(
                    "verify",
                    f"Verify the key claims and conclusions before answering: {goal}",
                    "research",
                    ("analyze",),
                ),
                PlanStep(
                    "synthesize",
                    f"Synthesize the verified findings into a concise answer for: {goal}",
                    "reasoning",
                    ("verify",),
                ),
            )
        elif task_type == "coding" or any(x in lower for x in ("build", "fix", "implement")):
            steps = (
                PlanStep("analyze", f"Analyze requirements and constraints: {goal}", "reasoning"),
                PlanStep("implement", goal, "coding", ("analyze",)),
                PlanStep("test", f"Test the proposed implementation for: {goal}", "coding", ("implement",)),
                PlanStep(
                    "review",
                    f"Review the implementation and test results for correctness: {goal}",
                    "reasoning",
                    ("test",),
                ),
                PlanStep(
                    "synthesize",
                    f"Summarize the implementation, test results, and remaining issues for: {goal}",
                    "reasoning",
                    ("review",),
                ),
            )
        elif any(x in lower for x in ("analyze", "recommend", "compare", "architecture", "evaluate")):
            steps = (
                PlanStep("analyze", goal, "reasoning"),
                PlanStep(
                    "review",
                    f"Critically review the analysis and identify risks or missing considerations: {goal}",
                    "reasoning",
                    ("analyze",),
                ),
                PlanStep(
                    "synthesize",
                    f"Produce a concise recommendation based on the analysis and review: {goal}",
                    "reasoning",
                    ("review",),
                ),
            )
        else:
            steps = (PlanStep("solve", goal, task_type),)

        return TaskPlan(goal=goal, steps=steps)
