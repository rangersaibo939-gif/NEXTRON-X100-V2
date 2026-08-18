"""Deterministic result checks used before an LLM judge is introduced."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Evaluation:
    accepted: bool
    score: int
    reasons: tuple[str, ...]


class ResultEvaluator:
    """Basic safety/quality gate for orchestration results."""

    def evaluate(self, text: str) -> Evaluation:
        reasons: list[str] = []
        if not text or not text.strip():
            reasons.append("empty response")
        if len(text.strip()) < 3:
            reasons.append("response too short")

        score = 100 if not reasons else max(0, 100 - 50 * len(reasons))
        return Evaluation(accepted=not reasons, score=score, reasons=tuple(reasons))
