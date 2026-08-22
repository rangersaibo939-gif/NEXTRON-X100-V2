"""Concrete Android SDK toolchain adapter for NEXTRON App Builder."""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from ..contracts import BuildArtifact, BuildLog, BuildRequest, BuildResult, BuildStage


@dataclass(frozen=True)
class AndroidSdkPaths:
    root: Path
    build_tools: Path
    platform: Path

    @classmethod
    def discover(cls, sdk_root: str | Path | None = None, api: int = 35) -> "AndroidSdkPaths":
        value = sdk_root or os.environ.get("ANDROID_SDK_ROOT") or os.environ.get("ANDROID_HOME")
        if not value:
            raise FileNotFoundError("ANDROID_SDK_ROOT/ANDROID_HOME is not configured")
        root = Path(value).expanduser()
        bt = root / "build-tools"
        versions = sorted((p for p in bt.iterdir() if p.is_dir()), reverse=True) if bt.exists() else []
        if not versions:
            raise FileNotFoundError(f"No build-tools found under {bt}")
        tools = next((p for p in versions if p.name.startswith(f"{api}.")), versions[0])
        platform = root / "platforms" / f"android-{api}"
        if not (platform / "android.jar").exists():
            platforms = sorted((p for p in (root / "platforms").glob("android-*") if p.is_dir()), reverse=True)
            if not platforms:
                raise FileNotFoundError(f"No Android platform found under {root / 'platforms'}")
            platform = platforms[0]
        return cls(root, tools, platform)

    def tool(self, name: str) -> Path:
        candidate = self.build_tools / name
        found = candidate if candidate.exists() else Path(shutil.which(name) or "")
        if not found or not found.exists():
            raise FileNotFoundError(f"Android build tool not found: {name}")
        return found


class ToolchainError(RuntimeError):
    def __init__(self, stage: BuildStage, message: str) -> None:
        self.stage = stage
        super().__init__(message)


class AndroidToolchainAdapter:
    """AAPT2 -> javac -> D8 -> APK package -> zipalign -> apksigner."""

    def __init__(self, sdk: AndroidSdkPaths, javac: str = "javac") -> None:
        self.sdk = sdk
        self.javac = shutil.which(javac) or javac
        self.zip = shutil.which("zip") or "zip"
        self.keytool = shutil.which("keytool") or "keytool"
        self.aapt2 = sdk.tool("aapt2")
        self.d8 = sdk.tool("d8")
        self.apksigner = sdk.tool("apksigner")
        self.zipalign = sdk.tool("zipalign")

    def build(self, request: BuildRequest) -> BuildResult:
        project = Path(request.working_directory).expanduser().resolve()
        out = project / ".nextron-build"
        out.mkdir(parents=True, exist_ok=True)
        logs: list[BuildLog] = []
        try:
            self._materialize(project, request, logs)
            resources = self._resources(project, out, logs)
            classes = self._compile(project, out, logs)
            dex = self._dex(classes, out, logs)
            unsigned = self._package(project, resources, dex, out, logs)
            aligned = self._align(unsigned, out, logs)
            signed = self._sign(aligned, out, request, logs)
            return BuildResult.success([BuildArtifact(BuildStage.SIGN, str(signed), "Signed Android APK")], logs)
        except ToolchainError as exc:
            logs.append(BuildLog(exc.stage, "ERROR", str(exc)))
            return BuildResult.failure(logs, str(exc))
        except Exception as exc:
            logs.append(BuildLog(BuildStage.PACKAGE, "ERROR", f"Unexpected toolchain error: {exc}"))
            return BuildResult.failure(logs, str(exc))

    def _materialize(self, project: Path, request: BuildRequest, logs: list[BuildLog]) -> None:
        main = project / "src" / "main"
        (main / "java").mkdir(parents=True, exist_ok=True)
        (main / "res").mkdir(parents=True, exist_ok=True)
        (main / "assets").mkdir(parents=True, exist_ok=True)
        if request.manifest:
            (main / "AndroidManifest.xml").write_text(request.manifest, encoding="utf-8")
        for rel, content in request.source_files.items():
            p = main / "java" / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
        for rel, content in request.resource_files.items():
            p = main / "res" / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
        for rel, content in request.asset_files.items():
            p = main / "assets" / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
        logs.append(BuildLog(BuildStage.PREPARE, "INFO", f"Workspace prepared: {project}"))

    def _resources(self, project: Path, out: Path, logs: list[BuildLog]) -> Path:
        stage = BuildStage.RESOURCE
        main = project / "src" / "main"
        manifest = main / "AndroidManifest.xml"
        if not manifest.exists():
            raise ToolchainError(stage, "AndroidManifest.xml not found")
        flat, generated = out / "flat", out / "generated"
        flat.mkdir(exist_ok=True)
        generated.mkdir(exist_ok=True)
        self._run([str(self.aapt2), "compile", "--dir", str(main / "res"), "-o", str(flat)], logs, stage)
        linked = out / "resources.ap_"
        args = [str(self.aapt2), "link", "-o", str(linked), "-I", str(self.sdk.platform / "android.jar"), "--manifest", str(manifest), "--java", str(generated)]
        self._run(args + sorted(str(p) for p in flat.rglob("*.flat")), logs, stage)
        return linked

    def _compile(self, project: Path, out: Path, logs: list[BuildLog]) -> Path:
        stage = BuildStage.COMPILE
        classes = out / "classes"
        classes.mkdir(exist_ok=True)
        sources = sorted((project / "src" / "main").rglob("*.java")) + sorted((out / "generated").rglob("*.java"))
        if not sources:
            raise ToolchainError(stage, "No Java sources found")
        self._run([self.javac, "-source", "8", "-target", "8", "-classpath", str(self.sdk.platform / "android.jar"), "-d", str(classes)] + [str(p) for p in sources], logs, stage)
        return classes

    def _dex(self, classes: Path, out: Path, logs: list[BuildLog]) -> Path:
        stage = BuildStage.DEX
        dex = out / "dex"
        dex.mkdir(exist_ok=True)
        files = [str(p) for p in classes.rglob("*.class")]
        if not files:
            raise ToolchainError(stage, "No class files produced")
        self._run([str(self.d8), "--output", str(dex), "--lib", str(self.sdk.platform / "android.jar")] + files, logs, stage)
        return dex

    def _package(self, project: Path, resources: Path, dex: Path, out: Path, logs: list[BuildLog]) -> Path:
        stage = BuildStage.PACKAGE
        apk = out / "unsigned.apk"
        shutil.copy2(resources, apk)
        self._run([self.zip, "-j", str(apk), str(dex / "classes.dex")], logs, stage)
        assets = project / "src" / "main" / "assets"
        for item in assets.rglob("*") if assets.exists() else []:
            if item.is_file():
                self._run([self.zip, "-j", str(apk), str(item)], logs, stage)
        return apk

    def _align(self, unsigned: Path, out: Path, logs: list[BuildLog]) -> Path:
        aligned = out / "aligned.apk"
        self._run([str(self.zipalign), "-f", "4", str(unsigned), str(aligned)], logs, BuildStage.PACKAGE)
        return aligned

    def _sign(self, aligned: Path, out: Path, request: BuildRequest, logs: list[BuildLog]) -> Path:
        stage = BuildStage.SIGN
        # Temporary debug keystore for the builder MVP. Production signing belongs in a later secure layer.
        keystore = out / "debug.keystore"
        if not keystore.exists():
            self._run([self.keytool, "-genkeypair", "-v", "-keystore", str(keystore), "-storepass", "android", "-keypass", "android", "-alias", "androiddebugkey", "-keyalg", "RSA", "-keysize", "2048", "-validity", "10000", "-dname", "CN=Android Debug,O=Android,C=US"], logs, stage)
        signed = out / f"{request.project_name or 'app'}-signed.apk"
        self._run([str(self.apksigner), "sign", "--ks", str(keystore), "--ks-pass", "pass:android", "--key-pass", "pass:android", "--ks-key-alias", "androiddebugkey", "--out", str(signed), str(aligned)], logs, stage)
        return signed

    @staticmethod
    def _run(command: Sequence[str], logs: list[BuildLog], stage: BuildStage) -> None:
        try:
            proc = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
        except OSError as exc:
            raise ToolchainError(stage, f"Unable to execute {command[0]}: {exc}") from exc
        for line in proc.stdout.splitlines():
            logs.append(BuildLog(stage, "INFO" if proc.returncode == 0 else "ERROR", line))
        if proc.returncode != 0:
            raise ToolchainError(stage, f"{stage.value} failed with exit code {proc.returncode}: {command[0]}")
