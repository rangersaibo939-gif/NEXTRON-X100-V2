from core.app_builder.project_generator import AndroidProjectGenerator
from core.app_builder.toolchain import ToolchainBackend, ToolchainCapabilities, ToolchainRegistry


class FakeAdapter:
    def build(self, request):
        return None


def test_project_generator_creates_android_sources(tmp_path):
    result = AndroidProjectGenerator().generate(
        str(tmp_path / "demo"), "com.nextron.demo", "NEXTRON Demo"
    )
    assert result.activity_class == "MainActivity"
    assert (result.root / "AndroidManifest.xml").exists()
    assert (result.root / "src/main/java/com/nextron/demo/MainActivity.java").exists()
    assert (result.root / "src/main/res/values/strings.xml").exists()


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
