"""NEXTRON App Builder contracts and orchestration primitives.

This module defines NEXTRON-owned interfaces for an on-device Android app
builder. It is intentionally independent of VibeApp source code; VibeApp is
used as an architectural reference only.
"""

from .contracts import BuildRequest, BuildResult, BuildStage, BuildStatus
from .pipeline import AppBuildPipeline

__all__ = [
    "AppBuildPipeline",
    "BuildRequest",
    "BuildResult",
    "BuildStage",
    "BuildStatus",
]
