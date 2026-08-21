"""Multi-agent execution layer for NEXTRON X-100.

Executes the deterministic Planner output through the existing Orchestrator,
keeps step outputs, enforces dependencies, and evaluates every result before
allowing the workflow to continue.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.evaluator import Evaluation, ResultEvaluator
from core.orchestrator import ExecutionResult, Orchestrator
from core.planner import PlanStep, TaskPlan


@dataclass(frozen=True)
class AgentStepResult:
    step: PlanStep
    execution: ExecutionResult
    evaluation: Evaluation


@dataclass(frozen=True)
class MultiAgentResult:
    goal: str
    steps: tuple[AgentStepResult, ...]
    final_text: str


class MultiAgentExecutor:
    """Run a TaskPlan as an ordered multi-agent workflow."""

    def __init__(self, orchestrator: Orchestrator, evaluator: ResultEvaluator | None = None) -> None:
        self.orchestrator = orchestrator
        self.evaluator = evaluator or ResultEvaluator()

    @staticmethod
    def _prompt(step: PlanStep, outputs: dict[str, str]) -> str:
        context = "\n\n".join(
            f"[{name}]\n{text}" for name, text in outputs.items()
        )
        if not context:
            return step.task
        return (
            f"Execute workflow step: {step.name}\n"
            f"Task: {step.task}\n\n"
            f"Results from completed steps:\n{context}"
        )

    def execute(self, plan: TaskPlan) -> MultiAgentResult:
        outputs: dict[str, str] = {}
        results: list[AgentStepResult] = []

        for step in plan.steps:
            missing = [dependency for dependency in step.depends_on if dependency not in outputs]
            if missing:
                raise RuntimeError(
                    f"Step '{step.name}' has unmet dependencies: {', '.join(missing)}"
                )

            execution = self.orchestrator.execute(self._prompt(step, outputs))
            evaluation = self.evaluator.evaluate(execution.text)
            if not evaluation.accepted:
                raise RuntimeError(
                    f"Step '{step.name}' produced an unacceptable result: "
                    + "; ".join(evaluation.reasons)
                )

            outputs[step.name] = execution.text
            results.append(AgentStepResult(step, execution, evaluation))

        if not results:
            raise RuntimeError("Task plan contains no executable steps")

        # Prefer the planner's final synthesis step when present; otherwise
        # return the last successful agent result.
        final_text = outputs.get("synthesize", results[-1].execution.text)
        return MultiAgentResult(plan.goal, tuple(results), final_text)
