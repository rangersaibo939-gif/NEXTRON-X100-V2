from pathlib import Path


def test_build_apk_stays_local():
    text = Path("tools/interactive_console.py").read_text(encoding="utf-8")
    assert "Intent.ACTION_VIEW" not in text
    assert "Opening GitHub Actions" not in text
    assert "APK build requested" in text
