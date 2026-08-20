"""Provider-neutral orchestration for NEXTRON's Android build engine.

Concrete Android compiler adapters will be added in later phases. This layer
keeps NEXTRON's AI orchestration independent from the compiler implementation.
"""

from dataclasses import dataclass
from typing import Callable, Optional, Protocol

from .contracts import BuildRequest, BuildResult, BuildStage


class BuildAdapter(Protocol):
    """Adapter implemented by the actual on-device Android toolchain."""

    def run_stage(self, stage: BuildStage, request: BuildRequest) -> BuildResult:
        ...


@dataclass
class AppBuildPipeline:
    """Runs the canonical NEXTRON app-build sequence.

    The sequence mirrors the proven on-device builder pattern while keeping
    all implementation code NEXTRON-owned and swappable.
    """

    adapter: BuildAdapter
    repair: Optional[Callable[[BuildRequest, BuildResult], BuildRequest]] = None
    max_repairs: int = 3

    stages: tuple[BuildStage, ...] = (
        BuildStage.PREPARE,
        BuildStage.RESOURCE,
        BuildStage.COMPILE,
        BuildStage.DEX,
        BuildStage.PACKAGE,
        BuildStage.SIGN,
    )

    def build(self, request: BuildRequest) -> BuildResult:
        current = request
        last_result: Optional[BuildResult] = None

        for attempt in range(self.max_repairs + 1):
            for stage in self.stages:
                result = self.adapter.run_stage(stage, current)
                result.repair_attempt = attempt
                last_result = result
                if result.status.value == "failed":
                    break
            else:
                return last_result  # type: ignore[return-value]

            if self.repair is None or attempt >= self.max_repairs:
                return last_result  # type: ignore[return-value]

            current = self.repair(current, last_result)

        return last_result  # type: ignore[return-value]
