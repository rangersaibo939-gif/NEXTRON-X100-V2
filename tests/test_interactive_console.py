from pathlib import Path

from tools.build_nextron_app import build_project


def test_generated_console_has_app_request_and_agent_actions(tmp_path: Path):
    root = build_project(str(tmp_path / "nextron"))
    activity = next(root.glob("app/src/main/java/**/MainActivity.kt")).read_text(encoding="utf-8")
    assert "What should NEXTRON build?" in activity
    assert "App request captured" in activity
    assert "Multi-brain plan ready: Planner → Coder → Reviewer" in activity
