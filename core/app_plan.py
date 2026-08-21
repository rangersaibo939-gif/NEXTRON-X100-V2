from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

_PACKAGE_RE = re.compile(r"^[a-z_][a-z0-9_]*(\.[a-z_][a-z0-9_]*)+$")


@dataclass(frozen=True)
class AppPlan:
    app_name: str
    package_name: str
    description: str
    platform: str
    screens: tuple[str, ...]
    features: tuple[str, ...]
    theme: dict[str, Any]
    data_model: dict[str, Any]
    actions: tuple[str, ...]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppPlan":
        if not isinstance(data, dict):
            raise ValueError("AppPlan must be a JSON object")

        required = (
            "app_name",
            "package_name",
            "description",
            "platform",
            "screens",
            "features",
            "theme",
            "data_model",
            "actions",
        )

        missing = [key for key in required if key not in data]
        if missing:
            raise ValueError(
                "AppPlan missing required fields: " + ", ".join(missing)
            )

        app_name = data["app_name"]
        package_name = data["package_name"]

        if not isinstance(app_name, str) or not app_name.strip():
            raise ValueError("app_name must be a non-empty string")

        if (
            not isinstance(package_name, str)
            or not _PACKAGE_RE.fullmatch(package_name)
        ):
            raise ValueError(f"Invalid Android package name: {package_name!r}")

        if data["platform"] != "android":
            raise ValueError("AppPlan platform must be 'android'")

        for key in ("screens", "features", "actions"):
            value = data[key]
            if not isinstance(value, list) or not all(
                isinstance(x, str) and x.strip() for x in value
            ):
                raise ValueError(
                    f"{key} must be a list of non-empty strings"
                )

        if not isinstance(data["theme"], dict):
            raise ValueError("theme must be an object")

        if not isinstance(data["data_model"], dict):
            raise ValueError("data_model must be an object")

        return cls(
            app_name=app_name.strip(),
            package_name=package_name,
            description=str(data["description"]),
            platform="android",
            screens=tuple(data["screens"]),
            features=tuple(data["features"]),
            theme=dict(data["theme"]),
            data_model=dict(data["data_model"]),
            actions=tuple(data["actions"]),
        )
