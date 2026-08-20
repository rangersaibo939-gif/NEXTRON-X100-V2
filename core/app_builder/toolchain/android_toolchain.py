"""Android SDK toolchain adapter for NEXTRON App Builder.

This adapter intentionally invokes standard Android SDK command-line tools instead
of depending on Gradle. It is designed to sit behind the NEXTRON App Builder
contracts and can run on Android/Termux or desktop Linux when the SDK is present.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from ..contracts import BuildArtifact, BuildRequest, BuildResult, BuildStage


@dataclass(frozen=True)
class AndroidSdkPaths:
    root: Path
    build_tools: Path
    platform: Path

    @classmethod
    def discover(cls, sdk_root: str | Path | None = None, api: int = 35) -> "AndroidSdkPaths":
        root_value = sdk_root or os.environ.get("ANDROID_SDK_ROOT") or os.environ.get("ANDROID_HOME")
        if not root_value:
            raise FileNotFoundError("ANDROID_SDK_ROOT/ANDROID_HOME is not configured")
        root = Path(root_value).expanduser()
        if not root.is_dir():
            raise FileNotFoundError(f"Android SDK not found: {root}")

        bt_root = root / "build-tools"
        versions = sorted((p for p in bt_root.iterdir() if p.is_dir()), reverse=True) if bt_root.exists() else []
        if not versions:
            raise FileNotFoundError(f"No Android build-tools found under {bt_root}")
        build_tools = next((p for p in versions if p.name.startswith(str(api) + ".")), versions[0])
        platform = root / "platforms" / f"android-{api}"
        if not (platform / "android.jar").exists():
            platforms = sorted((p for p in (root / "platforms").glob("android-*") if p.is_dir()), reverse=True)
            if not platforms:
                raise FileNotFoundError(f"No Android platform found under {root / 'platforms'}")
            platform = platforms[0]
        return cls(root=root, build_tools=build_tools, platform=platform)

    def tool(self, name: str) -> Path:
        candidate = self.build_tools / name
        if candidate.exists():
            return candidate
        found = shutil.which(name)
        if found:
            return Path(found)
        raise FileNotFoundError(f"Android build tool not found: {name}")


@dataclass
class ToolchainResult:
    success: bool
    apk: Path | None
    logs: list[str]
    failed_stage: BuildStage | None = None


class AndroidToolchainAdapter:
    """Concrete AAPT2 -> javac -> D8 -> package -> zipalign -> apksigner adapter."""

    def __init__(self, sdk: AndroidSdkPaths, java: str = "javac") -> None:
        self.sdk = sdk
        self.javac = shutil.which(java) or java
        self.aapt2 = sdk.tool("aapt2")
        self.d8 = sdk.tool("d8")
        self.apksigner = sdk.tool("apksigner")
        self.zipalign = sdk.tool("zipalign")

    def build(self, request: BuildRequest) -> BuildResult:
        project = Path(request.project_dir).expanduser().resolve()
        out = Path(request.output_dir).expanduser().resolve()
        out.mkdir(parents=True, exist_ok=True)
        logs: list[str] = []

        try:
            resources = self._resources(project, out, logs)
            classes = self._compile_java(project, resources, out, logs)
            dex = self._dex(classes, out, logs)
            unsigned = self._package(project, resources, dex, out, logs)
            aligned = self._align(unsigned, out, logs)
            signed = self._sign(aligned, out, request, logs)
            artifact = BuildArtifact(path=str(signed), description="Signed Android APK")
            return BuildResult.success(artifacts=[artifact], logs=logs)
        except ToolchainError as exc:
            logs.append(str(exc))
            return BuildResult.failure(stage=exc.stage, logs=logs)
        except Exception as exc:
            logs.append(f"UNEXPECTED: {exc}")
            return BuildResult.failure(stage=BuildStage.PACKAGE, logs=logs)

    def _resources(self, project: Path, out: Path, logs: list[str]) -> Path:
        stage = BuildStage.RESOURCE
        res = project / "src" / "main" / "res"
        manifest = project / "src" / "main" / "AndroidManifest.xml"
        if not manifest.exists():
            manifest = project / "AndroidManifest.xml"
        if not manifest.exists():
            raise ToolchainError(stage, "AndroidManifest.xml not found")
        flat = out / "flat"
        flat.mkdir(exist_ok=True)
        self._run([str(self.aapt2), "compile", "--dir", str(res), "-o", str(flat)], logs, stage)
        flats = sorted(str(p) for p in flat.rglob("*.flat"))
        linked = out / "resources.ap_"
        args = [str(self.aapt2), "link", "-o", str(linked), "-I", str(self.sdk.platform / "android.jar"), "--manifest", str(manifest), "--java", str(out / "generated")]
        self._run(args + flats, logs, stage)
        return linked

    def _compile_java(self, project: Path, resources: Path, out: Path, logs: list[str]) -> Path:
        stage = BuildStage.COMPILE
        classes = out / "classes"
        classes.mkdir(exist_ok=True)
        sources = sorted(project.rglob("*.java")) + sorted((out / "generated").rglob("*.java"))
        if not sources:
            raise ToolchainError(stage, "No Java sources found")
        cp = str(self.sdk.platform / "android.jar")
        self._run([self.javac, "-source", "8", "-target", "8", "-classpath", cp, "-d", str(classes)] + [str(p) for p in sources], logs, stage)
        return classes

    def _dex(self, classes: Path, out: Path, logs: list[str]) -> Path:
        stage = BuildStage.DEX
        dex = out / "dex"
        dex.mkdir(exist_ok=True)
        class_files = [str(p) for p in classes.rglob("*.class")]
        self._run([str(self.d8), "--output", str(dex), "--lib", str(self.sdk.platform / "android.jar")] + class_files, logs, stage)
        return dex

    def _package(self, project: Path, resources: Path, dex: Path, out: Path, logs: list[str]) -> Path:
        stage = BuildStage.PACKAGE
        unsigned = out / "unsigned.apk"
        shutil.copy2(resources, unsigned)
        self._run(["zip", "-j", str(unsigned), str(dex / "classes.dex")], logs, stage)
        assets = project / "src" / "main" / "assets"
        if assets.exists():
            for item in assets.rglob("*"):
                if item.is_file():
                    rel = item.relative_to(assets)
                    self._run(["zip", "-j", str(unsigned), str(item)], logs, stage)
                    logs.append(f"asset staged: {rel}")
        return unsigned

    def _align(self, unsigned: Path, out: Path, logs: list[str]) -> Path:
        aligned = out / "aligned.apk"
        self._run([str(self.zipalign), "-f", "4", str(unsigned), str(aligned)], logs, BuildStage.PACKAGE)
        return aligned

    def _sign(self, aligned: Path, out: Path, request: BuildRequest, logs: list[str]) -> Path:
        stage = BuildStage.SIGN
        signed = out / "app-signed.apk"
        keystore = Path(request.keystore_path).expanduser()
        args = [str(self.apksigner), "sign", "--ks", str(keystore), "--out", str(signed)]
        if request.keystore_password:
            args += ["--ks-pass", f"pass:{request.keystore_password}"]
        if request.key_alias:
            args += ["--ks-key-alias", request.key_alias]
        self._run(args + [str(aligned)], logs, stage)
        return signed

    @staticmethod
    def _run(command: Sequence[str], logs: list[str], stage: BuildStage) -> None:
        try:
            proc = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
        except OSError as exc:
            raise ToolchainError(stage, f"Unable to execute {command[0]}: {exc}") from exc
        logs.extend(proc.stdout.splitlines())
        if proc.returncode != 0:
            raise ToolchainError(stage, f"{stage.value} failed with exit code {proc.returncode}: {command[0]}")


class ToolchainError(RuntimeError):
    def __init__(self, stage: BuildStage, message: str) -> None:
        self.stage = stage
        super().__init__(message)
