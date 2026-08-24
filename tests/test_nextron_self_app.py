from pathlib import Path

from core.app_builder.project_generator import AndroidProjectGenerator


def test_nextron_self_app_generates_real_compose_project(tmp_path: Path):
    output = tmp_path / "nextron-app"
    AndroidProjectGenerator().generate(
        str(output),
        "com.nextron.x100",
        "NEXTRON X-100",
        description="AI-powered multi-brain app builder and autonomous build console.",
        screens=("Multi-Brain Dashboard", "Agent Tasks", "Build Status", "App History", "Settings"),
        features=("Multi-Brain orchestration", "Autonomous coding", "Build monitoring", "APK delivery"),
        theme={"mode": "dark"},
        data_model={"activeTask": "string", "buildStatus": "string", "artifactPath": "string"},
        actions=("Create App", "Run Agent", "Build APK", "Download APK"),
    )

    main = output / "app" / "src" / "main" / "java" / "com" / "nextron" / "x100" / "MainActivity.kt"
    manifest = output / "app" / "src" / "main" / "AndroidManifest.xml"
    plan = output / "app" / "src" / "main" / "assets" / "nextron_plan.json"

    assert main.exists()
    assert manifest.exists()
    assert plan.exists()

    source = main.read_text(encoding="utf-8")
    assert "Multi-Brain Dashboard" in source
    assert "Agent Tasks" in source
    assert "Build Status" in source
    assert "App History" in source
    assert "Settings" in source
    assert "APK delivery" in source
    assert "Build APK" in source
    assert "darkColorScheme" in source

    plan_text = plan.read_text(encoding="utf-8")
    assert '"app_name": "NEXTRON X-100"' in plan_text
    assert '"package_name": "com.nextron.x100"' in plan_text
