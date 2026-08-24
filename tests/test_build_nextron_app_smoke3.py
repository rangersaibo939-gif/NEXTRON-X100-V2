from pathlib import Path

from tools.build_nextron_app import build_project


def test_generated_nextron_source_exists(tmp_path: Path):
    output = build_project(str(tmp_path / "nextron"))
    assert list((output / "app" / "src" / "main").rglob("MainActivity.kt"))
