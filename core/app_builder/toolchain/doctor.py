"""Android toolchain diagnostics for NEXTRON App Builder."""

from dataclasses import dataclass
from pathlib import Path

from .android_toolchain import AndroidSdkPaths


@dataclass(frozen=True)
class ToolchainCheck:
    name: str
    available: bool
    path: str | None = None
    detail: str = ""


def diagnose(sdk_root: str | None = None, api: int = 35) -> list[ToolchainCheck]:
    checks: list[ToolchainCheck] = []
    try:
        sdk = AndroidSdkPaths.discover(sdk_root, api)
        checks.append(ToolchainCheck("Android SDK", True, str(sdk.root)))
        checks.append(ToolchainCheck("Android platform", (sdk.platform / "android.jar").exists(), str(sdk.platform)))
        for name in ("aapt2", "d8", "zipalign", "apksigner"):
            try:
                path = sdk.tool(name)
                checks.append(ToolchainCheck(name, True, str(path)))
            except FileNotFoundError as exc:
                checks.append(ToolchainCheck(name, False, detail=str(exc)))
    except FileNotFoundError as exc:
        checks.append(ToolchainCheck("Android SDK", False, detail=str(exc)))
    return checks
