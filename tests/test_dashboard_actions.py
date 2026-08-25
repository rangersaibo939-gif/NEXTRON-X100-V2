from pathlib import Path


def test_dashboard_actions_do_not_launch_browser():
    text = Path("tools/interactive_console.py").read_text(encoding="utf-8")
    assert "Intent.ACTION_VIEW" not in text
    assert "Opening GitHub Actions" not in text
    assert "APK build is handled by the latest Builder pipeline" in text
