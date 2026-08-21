"""Environment diagnostics for NEXTRON's on-device Android builder."""

import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass(frozen=True)
class ToolCheck:
    name: str
    path: str | None
    available: bool


class ToolchainDoctor:
    def _sdk_root(self) -> Path | None:
        value = os.environ.get("ANDROID_SDK_ROOT") or os.environ.get("ANDROID_HOME")
        return Path(value) if value else None

    def check(self) -> List[ToolCheck]:
        sdk = self._sdk_root()
        results: List[ToolCheck] = []
        if sdk:
            build_tools = sdk / "build-tools"
            versions = sorted([p for p in build_tools.iterdir() if p.is_dir()], reverse=True) if build_tools.exists() else []
            if versions:
                latest = versions[0]
                for name in ("aapt2", "d8", "zipalign", "apksigner"):
                    path = latest / name
                    results.append(ToolCheck(name, str(path), path.exists()))
            else:
                for name in ("aapt2", "d8", "zipalign", "apksigner"):
                    results.append(ToolCheck(name, None, False))
        else:
            for name in ("aapt2", "d8", "zipalign", "apksigner"):
                results.append(ToolCheck(name, None, False))

        results.append(ToolCheck("javac", shutil.which("javac"), shutil.which("javac") is not None))
        results.append(ToolCheck("java", shutil.which("java"), shutil.which("java") is not None))
        return results

    def healthy(self) -> bool:
        return all(item.available for item in self.check())
