from pathlib import Path


def test_interactive_console_contains_full_self_improvement_loop():
    text = Path("tools/interactive_console.py").read_text(encoding="utf-8")
    assert "Self-improvement pipeline" in text
    assert "Capabilities:" in text
    assert "Next gap:" in text
    assert "Development task:" in text
    assert "Planner ✓  Coder ✓  Reviewer ✓" in text
    assert "latest Builder pipeline will produce the APK" in text
    assert "Intent.ACTION_VIEW" not in text
