from core.app_builder.project_generator import AndroidProjectGenerator
from core.app_builder.toolchain import ToolchainBackend, ToolchainCapabilities, ToolchainRegistry


class FakeAdapter:
    def build(self, request):
        return None


def test_project_generator_creates_functional_compose_sources(tmp_path):
    result = AndroidProjectGenerator().generate(
        str(tmp_path / "demo"),
        "com.nextron.demo",
        "NEXTRON Demo",
        screens=("Home", "Details"),
        features=("Dark mode", "Totals"),
        actions=("Add Item", "Delete Item"),
        theme={"mode": "dark"},
    )

    assert result.activity_class == "MainActivity"
    manifest = result.root / "app/src/main/AndroidManifest.xml"
    source = result.root / "app/src/main/java/com/nextron/demo/MainActivity.kt"
    gradle = result.root / "app/build.gradle.kts"

    assert manifest.exists()
    assert source.exists()
    assert gradle.exists()

    kotlin = source.read_text(encoding="utf-8")
    assert "@Composable" in kotlin
    assert "var currentScreen by remember" in kotlin
    assert "currentScreen = 1" in kotlin
    assert 'Text("Home"' in kotlin
    assert 'Text("Details"' in kotlin
    assert 'Text("Dark mode"' in kotlin
    assert 'Text("Totals"' in kotlin
    assert 'lastAction = "Add Item"' in kotlin
    assert 'lastAction = "Delete Item"' in kotlin
    assert "darkColorScheme()" in kotlin
    assert "class MainActivity : ComponentActivity()" in kotlin
    assert ".java" not in kotlin


def test_project_generator_defaults_to_a_functional_home_screen(tmp_path):
    result = AndroidProjectGenerator().generate(
        str(tmp_path / "demo"), "com.nextron.demo", "NEXTRON Demo"
    )
    source = result.root / "app/src/main/java/com/nextron/demo/MainActivity.kt"
    kotlin = source.read_text(encoding="utf-8")

    assert 'Text("Home"' in kotlin
    assert "var currentScreen by remember" in kotlin
    assert "Primary Action" in kotlin


def test_toolchain_registry_prefers_direct_backend():
    registry = ToolchainRegistry({}, {})
    direct = FakeAdapter()
    registry.register(
        ToolchainBackend.DIRECT_ANDROID,
        direct,
        ToolchainCapabilities(
            ToolchainBackend.DIRECT_ANDROID,
            supports_kotlin=False,
            supports_compose=False,
            supports_java=True,
            supports_resources=True,
            supports_signing=True,
        ),
    )
    request = type("Request", (), {"source_files": {"Main.java": "class Main {}"}})()
    assert registry.select(request) is direct
