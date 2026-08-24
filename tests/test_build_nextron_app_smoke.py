from pathlib import Path

from tools.build_nextron_app import build_project


def test_build_nextron_app_smoke(tmp_path: Path):
    output = build_project(str(tmp_path / "nextron"))
    assert output.exists()
    assert (output / "app" / "src" / "main" / "AndroidManifest.xml").exists()
