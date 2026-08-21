"""Kotlin + Jetpack Compose Android project generator for NEXTRON Builder V2."""

from dataclasses import dataclass
from pathlib import Path
import re


@dataclass(frozen=True)
class GeneratedProject:
    root: Path
    package_name: str
    activity_class: str


class AndroidProjectGenerator:
    def generate(
        self,
        root: str,
        package_name: str,
        app_name: str = "NEXTRON App",
        screens: tuple[str, ...] = (),
        features: tuple[str, ...] = (),
        actions: tuple[str, ...] = (),
        theme: dict | None = None,
    ) -> GeneratedProject:

        target = Path(root)
        package_path = Path(*package_name.split("."))
        source_dir = target / "app" / "src" / "main" / "java" / package_path

        source_dir.mkdir(parents=True, exist_ok=True)

        safe_name = re.sub(r'[^A-Za-z0-9 _-]', '', app_name)
        safe_name = safe_name.replace('"', '\\"')

        settings = """pluginManagement {
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
    id("com.android.application") version "8.7.3" apply false
    id("org.jetbrains.kotlin.android") version "2.0.21" apply false
    id("org.jetbrains.kotlin.plugin.compose") version "2.0.21" apply false
}
"""

        app_gradle = f"""plugins {{
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
}}

android {{
    namespace = "{package_name}"
    compileSdk = 35

    defaultConfig {{
        applicationId = "{package_name}"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "1.0"
    }}

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
"""

        gradle_properties = """org.gradle.jvmargs=-Xmx2g -Dfile.encoding=UTF-8
android.useAndroidX=true
kotlin.code.style=official
"""

        manifest = f"""<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <application
        android:theme="@android:style/Theme.Material.Light.NoActionBar"
        android:label="{safe_name}">
        <activity
            android:name=".MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
"""

        screen_lines = "\n".join(
            f'                Text("{re.sub(r"[^A-Za-z0-9 _-]", "", screen)}")'
            for screen in screens
        )

        feature_lines = "\n".join(
            f'                Text("• {re.sub(r"[^A-Za-z0-9 _-]", "", feature)}")'
            for feature in features
        )

        action_lines = "\n".join(
            f'                Button(onClick = {{ }}) {{ Text("{re.sub(r"[^A-Za-z0-9 _-]", "", action)}") }}'
            for action in actions
        )

        activity_source = f"""package {package_name}

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

class MainActivity : ComponentActivity() {{
    override fun onCreate(savedInstanceState: Bundle?) {{
        super.onCreate(savedInstanceState)

        setContent {{
            MaterialTheme {{
                Surface(modifier = Modifier.fillMaxSize()) {{
                    NextronApp()
                }}
            }}
        }}
    }}
}}

@Composable
fun NextronApp() {{
    Column(
        modifier = Modifier.fillMaxSize(),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {{
        Text(
            text = "{safe_name}",
            style = MaterialTheme.typography.headlineMedium
        )

        Spacer(modifier = Modifier.height(20.dp))

{screen_lines}

        Spacer(modifier = Modifier.height(20.dp))

{feature_lines}

        Spacer(modifier = Modifier.height(20.dp))

{action_lines}
    }}
}}
"""

        (target / "settings.gradle.kts").write_text(
            settings,
            encoding="utf-8",
        )

        (target / "build.gradle.kts").write_text(
            root_gradle,
            encoding="utf-8",
        )

        (target / "gradle.properties").write_text(
            gradle_properties,
            encoding="utf-8",
        )

        app_dir = target / "app"
        app_dir.mkdir(parents=True, exist_ok=True)

        (app_dir / "build.gradle.kts").write_text(
            app_gradle,
            encoding="utf-8",
        )

        main_dir = app_dir / "src" / "main"
        main_dir.mkdir(parents=True, exist_ok=True)

        (main_dir / "AndroidManifest.xml").write_text(
            manifest,
            encoding="utf-8",
        )

        (source_dir / "MainActivity.kt").write_text(
            activity_source,
            encoding="utf-8",
        )

        return GeneratedProject(target, package_name, "MainActivity")
