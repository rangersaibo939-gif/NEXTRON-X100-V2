from pathlib import Path


def test_build_apk_does_not_open_github():
    text = Path("tools/interactive_console.py").read_text(encoding="utf-8")
    assert "Intent.ACTION_VIEW" not in text
    assert "Opening GitHub Actions" not in text
