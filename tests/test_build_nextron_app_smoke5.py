from tools.build_nextron_app import build_project


def test_generated_nextron_metadata(tmp_path):
    output = build_project(str(tmp_path / "nextron"))
    assert (output / "settings.gradle.kts").exists()
