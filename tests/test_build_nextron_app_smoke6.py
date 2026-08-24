from tools.build_nextron_app import build_project


def test_generated_nextron_resources(tmp_path):
    output = build_project(str(tmp_path / "nextron"))
    assert (output / "app" / "src" / "main").exists()
