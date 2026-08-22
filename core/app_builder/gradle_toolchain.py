"""System-Gradle backend for Kotlin/Compose Android projects."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Sequence

from .contracts import BuildArtifact, BuildLog, BuildRequest, BuildResult, BuildStage


class GradleToolchainAdapter:
    """Build an already-materialized Android project with system Gradle.

    This backend intentionally uses the project's Gradle files and does not
    download or execute generated scripts itself. NEXTRON only invokes the
    Gradle executable that is already installed on the device.
    """

    def __init__(self, gradle: str = "gradle") -> None:
        self.gradle = shutil.which(gradle) or gradle

    def build(self, request: BuildRequest) -> BuildResult:
        project = Path(request.working_directory).expanduser().resolve()
        logs: list[BuildLog] = []
        if not project.exists():
            return BuildResult.failure(
                logs, f"Gradle project directory does not exist: {project}", stage=BuildStage.PREPARE
            )
        if not (project / "settings.gradle.kts").exists() and not (project / "settings.gradle").exists():
            return BuildResult.failure(
                logs, "Gradle settings file not found", stage=BuildStage.PREPARE
            )

        task = ":app:assembleDebug" if request.build_type == "debug" else ":app:assembleRelease"
        try:
            proc = subprocess.run(
                [self.gradle, task, "--no-daemon", "--stacktrace"],
                cwd=project,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
        except OSError as exc:
            return BuildResult.failure(
                logs, f"Unable to execute Gradle: {exc}", stage=BuildStage.COMPILE
            )

        for line in proc.stdout.splitlines():
            logs.append(BuildLog(BuildStage.COMPILE, "INFO" if proc.returncode == 0 else "ERROR", line))

        if proc.returncode != 0:
            return BuildResult.failure(
                logs,
                f"Gradle build failed with exit code {proc.returncode}",
                stage=BuildStage.COMPILE,
            )

        candidates = sorted(project.glob("app/build/outputs/apk/**/*.apk"))
        if not candidates:
            return BuildResult.failure(
                logs, "Gradle completed but no APK was produced", stage=BuildStage.PACKAGE
            )
        apk = candidates[-1]
        return BuildResult.success(
            [BuildArtifact(BuildStage.PACKAGE, str(apk), "Gradle-built Android APK")], logs
        )


__all__ = ["GradleToolchainAdapter"]
