"""NEXTRON-owned contracts for the Android app build pipeline."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class BuildStage(str, Enum):
    PREPARE = "prepare"
    RESOURCE = "resource"
    COMPILE = "compile"
    DEX = "dex"
    PACKAGE = "package"
    SIGN = "sign"
    INSTALL = "install"


class BuildStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass(frozen=True)
class BuildRequest:
    project_id: str
    project_name: str
    package_name: str
    working_directory: str
    source_files: Dict[str, str] = field(default_factory=dict)
    resource_files: Dict[str, str] = field(default_factory=dict)
    asset_files: Dict[str, str] = field(default_factory=dict)
    manifest: Optional[str] = None
    min_sdk: int = 29
    target_sdk: int = 36
    version_code: int = 1
    version_name: str = "1.0"
    build_type: str = "debug"


@dataclass(frozen=True)
class BuildLog:
    stage: BuildStage
    level: str
    message: str
    source_path: Optional[str] = None
    line: Optional[int] = None


@dataclass(frozen=True)
class BuildArtifact:
    stage: BuildStage
    path: str
    description: str


@dataclass
class BuildResult:
    status: BuildStatus
    artifacts: List[BuildArtifact] = field(default_factory=list)
    logs: List[BuildLog] = field(default_factory=list)
    error_message: Optional[str] = None
    repair_attempt: int = 0

    @classmethod
    def success(cls, artifacts: List[BuildArtifact], logs: List[BuildLog]) -> "BuildResult":
        return cls(BuildStatus.SUCCESS, artifacts, logs)

    @classmethod
    def failure(
        cls,
        logs: List[BuildLog],
        error_message: str,
        repair_attempt: int = 0,
    ) -> "BuildResult":
        return cls(BuildStatus.FAILED, [], logs, error_message, repair_attempt)
