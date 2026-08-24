from pathlib import Path

from tools.build_nextron_app import build_project


def test_generated_nextron_plan_exists(tmp_path: Path):
    output = build_project(str(tmp_path / "nextron"))
    assert (output / "app" / "src" / "main" / "assets" / "nextron_plan.json").exists()
