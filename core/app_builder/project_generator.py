"""Kotlin + Jetpack Compose Android project generator for NEXTRON Builder V2."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class GeneratedProject:
    root: Path
    package_name: str
    activity_class: str


class AndroidProjectGenerator:
    """Materialize a deterministic Kotlin/Compose project from an AppPlan."""

    def generate(
        self,
        root: str,
        package_name: str,
        app_name: str = "NEXTRON App",
        screens: tuple[str, ...] = (),
        features: tuple[str, ...] = (),
        actions: tuple[str, ...] = (),
        theme: dict[str, Any] | None = None,
        data_model: dict[str, Any] | None = None,
        description: str = "",
    ) -> GeneratedProject:
        target = Path(root)
        package_path = Path(*package_name.split("."))
        source_dir = target / "app" / "src" / "main" / "java" / package_path
        source_dir.mkdir(parents=True, exist_ok=True)

        screens = tuple(screens) or ("Home",)
        features = tuple(features)
        actions = tuple(actions)
        theme = dict(theme or {})
        data_model = dict(data_model or {})

        def clean(value: str) -> str:
            return re.sub(r"[^A-Za-z0-9 _-]", "", str(value)).strip()

        def kotlin_string(value: Any) -> str:
            return (
                str(value)
                .replace("\\", "\\\\")
                .replace('"', '\\"')
                .replace("\n", " ")
            )

        safe_name = kotlin_string(clean(app_name) or "NEXTRON App")
        safe_description = kotlin_string(description)
        dark_value = str(theme.get("mode", theme.get("dark", ""))).lower()
        use_dark_theme = dark_value in {"dark", "true", "night"} or "dark" in dark_value

        settings = """import org.gradle.api.initialization.resolve.RepositoriesMode

pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "NEXTRONGenerated"
include(":app")
"""

        root_gradle = """plugins {
    id("com.android.application") version "8.9.1" apply false
    id("org.jetbrains.kotlin.plugin.compose") version "2.0.21" apply false
}
"""

        app_gradle = f"""plugins {{
    id("com.android.application")
    id("org.jetbrains.kotlin.plugin.compose")
}}

android {{
    namespace = "{package_name}"
    compileSdk = 36
    defaultConfig {{
        applicationId = "{package_name}"
        minSdk = 26
        targetSdk = 36
        versionCode = 1
        versionName = "1.0"
    }}
    buildFeatures {{
        compose = true
    }}
}}

dependencies {{
    implementation(platform("androidx.compose:compose-bom:2025.08.00"))
    implementation("androidx.activity:activity-compose:1.11.0")
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")
    debugImplementation("androidx.compose.ui:ui-tooling")
}}
"""

        gradle_properties = """org.gradle.jvmargs=-Xmx2g -Dfile.encoding=UTF-8
android.useAndroidX=true
kotlin.code.style=official
"""

        manifest = f"""<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <application android:theme="@android:style/Theme.Material.Light.NoActionBar" android:label="{safe_name}">
        <activity android:name=".MainActivity" android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
"""

        nav_lines = "\n".join(
            f'                    Button(onClick = {{ currentScreen = {index} }}) {{ Text("{kotlin_string(clean(screen) or f"Screen {index + 1}")}") }}'
            for index, screen in enumerate(screens)
        )

        feature_lines = "\n".join(
            f'                        Text("• {kotlin_string(clean(feature))}")'
            for feature in features
            if clean(feature)
        ) or '                        Text("Ready to use")'

        data_lines = "\n".join(
            f'                        Text("• {kotlin_string(key)}: {kotlin_string(value)}")'
            for key, value in data_model.items()
        ) or '                        Text("No data model fields")'

        action_lines = "\n".join(
            f'                        Button(onClick = {{ lastAction = "{kotlin_string(clean(action) or f"Action {index + 1}")}"; actionCount++ }}) {{ Text("{kotlin_string(clean(action) or f"Action {index + 1}")}") }}'
            for index, action in enumerate(actions)
        ) or '                        Button(onClick = { actionCount++ }) { Text("Primary Action") }'

        screen_cases = []
        for index, screen in enumerate(screens):
            title = kotlin_string(clean(screen) or f"Screen {index + 1}")
            screen_cases.append(
                f'''                    {index} -> Column(
                        modifier = Modifier.fillMaxSize(),
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.Center
                    ) {{
                        Text("{title}", style = MaterialTheme.typography.headlineSmall)
                        Spacer(modifier = Modifier.height(12.dp))
                        Text("{safe_name}")
                        if ("{safe_description}".isNotEmpty()) {{
                            Spacer(modifier = Modifier.height(8.dp))
                            Text("{safe_description}")
                        }}
                        Spacer(modifier = Modifier.height(16.dp))
{feature_lines}
                        Spacer(modifier = Modifier.height(16.dp))
                        Text("Data model", style = MaterialTheme.typography.titleMedium)
{data_lines}
                        Spacer(modifier = Modifier.height(20.dp))
{action_lines}
                        if (lastAction.isNotEmpty()) {{
                            Spacer(modifier = Modifier.height(12.dp))
                            Text("Last action: ${{lastAction}} (${{actionCount}})")
                        }}
                    }}'''
            )
        cases = "\n\n".join(screen_cases)

        activity_source = f'''package {package_name}

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

class MainActivity : ComponentActivity() {{
    override fun onCreate(savedInstanceState: Bundle?) {{
        super.onCreate(savedInstanceState)
        setContent {{ NextronApp() }}
    }}
}}

@Composable
fun NextronApp() {{
    var currentScreen by remember {{ mutableIntStateOf(0) }}
    var actionCount by remember {{ mutableIntStateOf(0) }}
    var lastAction by remember {{ mutableStateOf("") }}
    val colors = if ({str(use_dark_theme).lower()}) darkColorScheme() else lightColorScheme()

    MaterialTheme(colorScheme = colors) {{
        Surface(modifier = Modifier.fillMaxSize()) {{
            Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {{
                Text("{safe_name}", style = MaterialTheme.typography.headlineMedium)
                Spacer(modifier = Modifier.height(12.dp))
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {{
{nav_lines}
                }}
                Spacer(modifier = Modifier.height(20.dp))
                when (currentScreen) {{
{cases}
                    else -> currentScreen = 0
                }}
            }}
        }}
    }}
}}
'''

        plan_asset = {
            "app_name": app_name,
            "package_name": package_name,
            "description": description,
            "platform": "android",
            "screens": list(screens),
            "features": list(features),
            "theme": theme,
            "data_model": data_model,
            "actions": list(actions),
        }

        (target / "settings.gradle.kts").write_text(settings, encoding="utf-8")
        (target / "build.gradle.kts").write_text(root_gradle, encoding="utf-8")
        (target / "gradle.properties").write_text(gradle_properties, encoding="utf-8")
        app_dir = target / "app"
        app_dir.mkdir(parents=True, exist_ok=True)
        (app_dir / "build.gradle.kts").write_text(app_gradle, encoding="utf-8")
        main_dir = app_dir / "src" / "main"
        main_dir.mkdir(parents=True, exist_ok=True)
        (main_dir / "AndroidManifest.xml").write_text(manifest, encoding="utf-8")
        assets_dir = main_dir / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        (assets_dir / "nextron_plan.json").write_text(
            json.dumps(plan_asset, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        (source_dir / "MainActivity.kt").write_text(activity_source, encoding="utf-8")
        return GeneratedProject(target, package_name, "MainActivity")
