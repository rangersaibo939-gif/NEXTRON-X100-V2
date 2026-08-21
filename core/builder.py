"""NEXTRON Builder V2 foundation.

Turns a structured app specification into a reproducible project workspace.
The builder deliberately does not execute arbitrary generated code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json
import re
from typing import Iterable


_NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{1,63}$")


@dataclass(frozen=True)
class FileSpec:
    path: str
    content: str


@dataclass(frozen=True)
class AppSpec:
    name: str
    platform: str = "python"
    description: str = ""
    files: tuple[FileSpec, ...] = field(default_factory=tuple)

    def validate(self) -> None:
        if not _NAME_RE.fullmatch(self.name):
            raise ValueError("name must be 2-64 characters and contain only letters, numbers, '-' or '_'")
        if self.platform not in {"python", "web", "android"}:
            raise ValueError(f"unsupported platform: {self.platform}")
        seen: set[str] = set()
        for item in self.files:
            path = Path(item.path)
            if path.is_absolute() or ".." in path.parts:
                raise ValueError(f"unsafe file path: {item.path}")
            normalized = path.as_posix()
            if normalized in seen:
                raise ValueError(f"duplicate file path: {item.path}")
            seen.add(normalized)


class ProjectBuilder:
    """Materialize an AppSpec into a clean project directory."""

    def build(self, spec: AppSpec, destination: str | Path) -> Path:
        spec.validate()
        root = Path(destination).expanduser().resolve()
        root.mkdir(parents=True, exist_ok=True)

        manifest = {
            "name": spec.name,
            "platform": spec.platform,
            "description": spec.description,
            "files": [f.path for f in spec.files],
        }
        self._write(root / "nextron.project.json", json.dumps(manifest, indent=2) + "\n")

        for item in spec.files:
            target = (root / item.path).resolve()
            if root not in target.parents:
                raise ValueError(f"unsafe file path: {item.path}")
            self._write(target, item.content)
        return root

    @staticmethod
    def _write(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def app_spec_from_dict(data: dict) -> AppSpec:
    """Parse the provider/LLM-neutral builder contract."""
    files: Iterable[FileSpec] = (
        FileSpec(path=str(item["path"]), content=str(item.get("content", "")))
        for item in data.get("files", [])
    )
    spec = AppSpec(
        name=str(data["name"]),
        platform=str(data.get("platform", "python")),
        description=str(data.get("description", "")),
        files=tuple(files),
    )
    spec.validate()
    return spec
