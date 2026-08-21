from pathlib import Path

import pytest

from core.builder import AppSpec, FileSpec, ProjectBuilder, android_app_spec, app_spec_from_dict


def test_builds_project_and_manifest(tmp_path: Path):
    spec = AppSpec(
        name="hello-app",
        platform="python",
        description="test app",
        files=(FileSpec("src/main.py", "print('hello')\n"),),
    )

    root = ProjectBuilder().build(spec, tmp_path / "hello")

    assert (root / "src/main.py").read_text() == "print('hello')\n"
    manifest = (root / "nextron.project.json").read_text()
    assert '"name": "hello-app"' in manifest


def test_rejects_traversal():
    spec = AppSpec(name="safe-app", files=(FileSpec("../escape.py", "bad"),))
    with pytest.raises(ValueError, match="unsafe file path"):
        spec.validate()


def test_rejects_duplicate_paths():
    spec = AppSpec(
        name="safe-app",
        files=(FileSpec("main.py", "a"), FileSpec("main.py", "b")),
    )
    with pytest.raises(ValueError, match="duplicate"):
        spec.validate()


def test_parses_structured_contract():
    spec = app_spec_from_dict({
        "name": "demo",
        "platform": "web",
        "files": [{"path": "index.html", "content": "<h1>Demo</h1>"}],
    })
    assert spec.name == "demo"
    assert spec.platform == "web"
    assert spec.files[0].path == "index.html"


def test_rejects_unknown_platform():
    with pytest.raises(ValueError, match="unsupported platform"):
        AppSpec(name="demo", platform="ios").validate()


def test_android_app_spec_generates_compose_project():
    spec = android_app_spec(
        "Reaction-Battle",
        "com.nextron.reactionbattle",
        "NEXTRON reaction game",
    )

    assert spec.platform == "android"
    paths = {item.path for item in spec.files}
    assert "settings.gradle.kts" in paths
    assert "build.gradle.kts" in paths
    assert "app/build.gradle.kts" in paths
    assert "app/src/main/AndroidManifest.xml" in paths
    assert "app/src/main/java/com/nextron/reactionbattle/MainActivity.kt" in paths

    root = ProjectBuilder().build(spec, Path("/tmp/nextron-builder-test"))
    assert (root / "app/build.gradle.kts").exists()
    assert "com.android.application" in (root / "build.gradle.kts").read_text()
    assert "ReactionBattleActivity" in (root / "app/src/main/java/com/nextron/reactionbattle/MainActivity.kt").read_text()


def test_android_app_spec_rejects_invalid_package():
    with pytest.raises(ValueError, match="package_name"):
        android_app_spec("demo", "not-a-package")
