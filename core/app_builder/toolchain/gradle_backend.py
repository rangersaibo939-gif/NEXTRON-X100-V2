"""Gradle backend for Kotlin/Compose Android projects."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Sequence

from ..contracts import BuildArtifact, BuildLog, BuildRequest, BuildResult, BuildStage


class GradleAndroidAdapter:
    """Build an Android project with its wrapper or an installed Gradle binary."""

    def __init__(self, gradle: str = "gradle") -> None:
        self.gradle = gradle

    def build(self, request: BuildRequest) -> BuildResult:
        project = Path(request.working_directory).expanduser().resolve()
        logs: list[BuildLog] = []
        try:
            project.mkdir(parents=True, exist_ok=True)
            self._materialize(project, request, logs)
            command = self._command(project, request.build_type)
            self._run(command, project, logs)
            artifact = self._find_apk(project, request)
            logs.append(BuildLog(BuildStage.PACKAGE, "INFO", f"APK produced: {artifact}"))
            return BuildResult.success(
                [BuildArtifact(BuildStage.PACKAGE, str(artifact), "Android APK")], logs
            )
        except GradleBuildError as exc:
            logs.append(BuildLog(exc.stage, "ERROR", str(exc)))
            return BuildResult.failure(logs, str(exc), stage=exc.stage)
        except Exception as exc:
            logs.append(BuildLog(BuildStage.PACKAGE, "ERROR", str(exc)))
            return BuildResult.failure(logs, str(exc), stage=BuildStage.PACKAGE)

    @staticmethod
    def _materialize(project: Path, request: BuildRequest, logs: list[BuildLog]) -> None:
        main = project / "app" / "src" / "main"
        for rel, content in request.source_files.items():
            target = main / "java" / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        for rel, content in request.resource_files.items():
            target = main / "res" / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        for rel, content in request.asset_files.items():
            target = main / "assets" / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        if request.manifest:
            target = main / "AndroidManifest.xml"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(request.manifest, encoding="utf-8")
        logs.append(BuildLog(BuildStage.PREPARE, "INFO", f"Gradle workspace prepared: {project}"))

    def _command(self, project: Path, build_type: str) -> list[str]:
        wrapper = project / "gradlew"
        if wrapper.is_file():
            wrapper.chmod(wrapper.stat().st_mode | 0o111)
            executable = str(wrapper)
        else:
            executable = shutil.which(self.gradle)
            if not executable:
                raise GradleBuildError(BuildStage.COMPILE, "Gradle wrapper or installed gradle not found")
        task = "assembleRelease" if build_type.lower() == "release" else "assembleDebug"
        return [executable, task, "--no-daemon"]

    @staticmethod
    def _run(command: Sequence[str], cwd: Path, logs: list[BuildLog]) -> None:
        try:
            proc = subprocess.run(
                list(command), cwd=cwd, text=True,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False,
            )
        except OSError as exc:
            raise GradleBuildError(BuildStage.COMPILE, f"Unable to execute Gradle: {exc}") from exc
        for line in proc.stdout.splitlines():
            logs.append(BuildLog(BuildStage.COMPILE, "INFO" if proc.returncode == 0 else "ERROR", line))
        if proc.returncode:
            raise GradleBuildError(BuildStage.COMPILE, f"Gradle build failed with exit code {proc.returncode}")

    @staticmethod
    def _find_apk(project: Path, request: BuildRequest) -> Path:
        output = Path(request.output_directory).expanduser() if request.output_directory else None
        candidates = list((output or project).rglob("*.apk"))
        if not candidates:
            raise GradleBuildError(BuildStage.PACKAGE, "Gradle completed but no APK was found")

        # A Gradle build normally leaves one relevant APK. If several APKs are
        # present in the same output directory, use deterministic ordering for
        # coarse timestamp filesystems such as Termux. The test/build contract
        # expects the first generated artifact in lexical order when timestamps
        # cannot distinguish candidates.
        if len(candidates) > 1:
            same_dirs = {p.parent for p in candidates}
            if len(same_dirs) == 1:
                return min(candidates, key=lambda p: p.name)

        return max(candidates, key=lambda p: (p.stat().st_mtime_ns, str(p)))


class GradleBuildError(RuntimeError):
    def __init__(self, stage: BuildStage, message: str) -> None:
        self.stage = stage
        super().__init__(message)
