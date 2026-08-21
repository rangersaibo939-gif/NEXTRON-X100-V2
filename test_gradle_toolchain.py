from pathlib import Path

from core.app_builder.contracts import BuildRequest, BuildStatus
from core.app_builder.gradle_toolchain import GradleToolchainAdapter
from core.app_builder.toolchain import ToolchainBackend, ToolchainCapabilities, ToolchainRegistry


class FakeAdapter:
    def build(self, request):
        return None


def test_registry_routes_kotlin_to_gradle():
    direct = FakeAdapter()
    gradle = FakeAdapter()
    registry = ToolchainRegistry({}, {})
    registry.register(
        ToolchainBackend.DIRECT_ANDROID,
        direct,
        ToolchainCapabilities(ToolchainBackend.DIRECT_ANDROID, False, False, True, True, True),
    )
    registry.register(
        ToolchainBackend.GRADLE,
        gradle,
        ToolchainCapabilities(ToolchainBackend.GRADLE, True, True, True, True, True),
    )
    request = BuildRequest(
        project_id="demo",
        project_name="demo",
        package_name="com.nextron.demo",
        working_directory="/tmp/demo",
        source_files={"com/nextron/demo/MainActivity.kt": "class MainActivity"},
    )
    assert registry.select(request) is gradle


def test_gradle_backend_reports_missing_project(tmp_path: Path):
    result = GradleToolchainAdapter(gradle="definitely-not-installed").build(
        BuildRequest("demo", "demo", "com.nextron.demo", str(tmp_path / "missing"))
    )
    assert result.status is BuildStatus.FAILED
    assert result.failed_stage is not None
