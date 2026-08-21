from pathlib import Path

import pytest

from core.builder import AppSpec, FileSpec, ProjectBuilder, app_spec_from_dict


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
