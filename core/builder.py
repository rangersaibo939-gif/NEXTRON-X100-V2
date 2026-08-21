"""NEXTRON Builder V2 foundation and Android project templates."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import json
import re
from typing import Iterable

_NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{1,63}$")
_PACKAGE_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)+$")

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
    def build(self, spec: AppSpec, destination: str | Path) -> Path:
        spec.validate()
        root = Path(destination).expanduser().resolve()
        root.mkdir(parents=True, exist_ok=True)
        manifest = {"name": spec.name, "platform": spec.platform, "description": spec.description, "files": [f.path for f in spec.files]}
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
    files: Iterable[FileSpec] = (FileSpec(path=str(item["path"]), content=str(item.get("content", ""))) for item in data.get("files", []))
    spec = AppSpec(name=str(data["name"]), platform=str(data.get("platform", "python")), description=str(data.get("description", "")), files=tuple(files))
    spec.validate()
    return spec

def android_app_spec(name: str, package_name: str, description: str = "") -> AppSpec:
    """Return a minimal Android/Jetpack Compose project ready for Gradle generation."""
    if not _NAME_RE.fullmatch(name):
        raise ValueError("invalid app name")
    if not _PACKAGE_RE.fullmatch(package_name):
        raise ValueError("package_name must be a dotted Android package name")
    title = name.replace("-", " ").replace("_", " ").title()
    activity = re.sub(r"[^A-Za-z0-9]", "", name)
    pkg_path = package_name.replace(".", "/")
    files = (
        FileSpec("settings.gradle.kts", f'''pluginManagement {{ repositories {{ google(); mavenCentral(); gradlePluginPortal() }} }}
dependencyResolutionManagement {{ repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS); repositories {{ google(); mavenCentral() }} }}
rootProject.name = "{name}"
include(":app")
'''),
        FileSpec("build.gradle.kts", '''plugins {
    id("com.android.application") version "8.7.3" apply false
    id("org.jetbrains.kotlin.android") version "2.0.21" apply false
    id("org.jetbrains.kotlin.plugin.compose") version "2.0.21" apply false
}
'''),
        FileSpec("gradle.properties", "org.gradle.jvmargs=-Xmx2g -Dfile.encoding=UTF-8\nandroid.useAndroidX=true\nkotlin.code.style=official\n"),
        FileSpec("app/build.gradle.kts", f'''plugins {{
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
}}
android {{
    namespace = "{package_name}"
    compileSdk = 35

    defaultConfig {{ applicationId = "{package_name}"; minSdk = 26; targetSdk = 35; versionCode = 1; versionName = "1.0" }}

    compileOptions {{
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }}

    kotlinOptions {{
        jvmTarget = "17"
    }}
}}
dependencies {{
    implementation(platform("androidx.compose:compose-bom:2024.12.01"))
    implementation("androidx.activity:activity-compose:1.10.0")
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")
    debugImplementation("androidx.compose.ui:ui-tooling")
}}
'''),
        FileSpec("app/src/main/AndroidManifest.xml", f'''<manifest xmlns:android="http://schemas.android.com/apk/res/android"><application android:theme="@style/Theme.Nextron" android:label="{title}"><activity android:name=".{activity}Activity" android:exported="true"><intent-filter><action android:name="android.intent.action.MAIN"/><category android:name="android.intent.category.LAUNCHER"/></intent-filter></activity></application></manifest>
'''),
        FileSpec("app/src/main/res/values/styles.xml", '<resources><style name="Theme.Nextron" parent="android:style/Theme.Material.Light.NoActionBar"/></resources>\n'),
        FileSpec(f"app/src/main/java/{pkg_path}/MainActivity.kt", f'''package {package_name}

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text

class {activity}Activity : ComponentActivity() {{
    override fun onCreate(savedInstanceState: Bundle?) {{
        super.onCreate(savedInstanceState)
        setContent {{ MaterialTheme {{ Surface {{ Text("{title}") }} }} }}
    }}
}}
'''),
    )
    return AppSpec(name=name, platform="android", description=description, files=files)
