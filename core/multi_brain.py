from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BrainResult:
    role: str
    output: str


class MultiBrain:
    """Deterministic local orchestration that works without paid model credits."""

    def run(self, request: str) -> tuple[BrainResult, ...]:
        text = request.strip()
        if not text:
            raise ValueError("request must not be empty")
        return (
            BrainResult("planner", f"Plan: define the Android app structure and user flow for: {text}"),
            BrainResult("coder", "Coder: generate the smallest testable Android implementation from the plan."),
            BrainResult("reviewer", "Reviewer: validate the plan, implementation scope, and build readiness."),
        )
