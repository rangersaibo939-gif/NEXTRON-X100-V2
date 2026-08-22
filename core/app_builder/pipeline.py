"""Provider-neutral orchestration for NEXTRON's Android build engine."""

from dataclasses import dataclass
from typing import Callable, Optional, Protocol

from .contracts import BuildRequest, BuildResult


class BuildAdapter(Protocol):
    """Concrete adapter that turns a NEXTRON project into a build result."""

    def build(self, request: BuildRequest) -> BuildResult:
        ...


@dataclass
class AppBuildPipeline:
    """Runs a build and optionally asks an AI repair callback to retry it."""

    adapter: BuildAdapter
    repair: Optional[Callable[[BuildRequest, BuildResult], BuildRequest]] = None
    max_repairs: int = 3

    def build(self, request: BuildRequest) -> BuildResult:
        current = request
        for attempt in range(self.max_repairs + 1):
            result = self.adapter.build(current)
            result.repair_attempt = attempt
            if result.status.value == "success":
                return result
            if self.repair is None or attempt >= self.max_repairs:
                return result
            current = self.repair(current, result)
        return result
