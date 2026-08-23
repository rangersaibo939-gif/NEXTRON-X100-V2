def test_nextron_main_wires_multi_brain_into_planner(monkeypatch, tmp_path, capsys):
    import core.nextron as nextron
    from core.app_builder.contracts import BuildArtifact, BuildResult, BuildStage
    from core.app_plan import AppPlan

    calls = []
    providers = {"reasoner": object(), "coder": object(), "researcher": object()}

    def fake_build_providers():
        calls.append("providers")
        return providers

    def fake_multi_brain(task, supplied):
        assert task == "Build a calculator"
        assert supplied is providers
        calls.append("multi-brain")
        return "CONSENSUS: build a calculator"

    class FakePlanner:
        def __init__(self, provider):
            calls.append(("planner-init", provider))
            assert provider is providers["reasoner"]

        def plan(self, task):
            calls.append(("planner-plan", task))
            assert task == "CONSENSUS: build a calculator"
            return AppPlan(
                app_name="Calculator",
                package_name="com.nextron.calculator",
                description="A calculator",
                platform="android",
                screens=("Home",),
                features=("calculate",),
                theme={"mode": "dark"},
                data_model={},
                actions=("calculate",),
            )

    class FakeGenerated:
        root = tmp_path / "generated"

    class FakeGenerator:
        def generate(self, *args, **kwargs):
            calls.append("generate")
            FakeGenerated.root.mkdir(parents=True, exist_ok=True)
            return FakeGenerated()

    class FakePipeline:
        def __init__(self, *args, **kwargs):
            calls.append("pipeline-init")

        def build(self, request):
            calls.append("build")
            apk = tmp_path / "calculator.apk"
            apk.write_bytes(b"fake-apk")
            return BuildResult.success(
                [BuildArtifact(BuildStage.PACKAGE, str(apk), "Android APK")], []
            )

    monkeypatch.setattr(nextron, "build_providers", fake_build_providers)
    monkeypatch.setattr(nextron, "_multi_brain_context", fake_multi_brain)
    monkeypatch.setattr(nextron, "AIPlanner", FakePlanner)
    monkeypatch.setattr(nextron, "AndroidProjectGenerator", FakeGenerator)
    monkeypatch.setattr(nextron, "AppBuildPipeline", FakePipeline)
    monkeypatch.setattr(nextron, "_copy_apk_to_downloads", lambda *args: None)
    monkeypatch.setattr(nextron, "_install_and_smoke_test", lambda *args: False)
    monkeypatch.chdir(tmp_path)

    assert nextron.main("Build a calculator") == 0
    assert calls[:4] == [
        "providers",
        "multi-brain",
        ("planner-init", providers["reasoner"]),
        ("planner-plan", "CONSENSUS: build a calculator"),
    ]
    assert "generate" in calls
    assert "build" in calls

    output = capsys.readouterr().out
    assert "Stage 1/4: Multi-Brain planning..." in output
    assert "BUILD SUCCESS" in output
    assert "NEXTRON BUILD COMPLETE" in output


def test_multi_brain_module_imports():
    from core.multi_brain import MultiBrainOrchestrator

    assert MultiBrainOrchestrator.ROLE_CAPABILITIES["coder"] == "coding"
    assert MultiBrainOrchestrator.ROLE_CAPABILITIES["reasoner"] == "reasoning"
    assert MultiBrainOrchestrator.ROLE_CAPABILITIES["researcher"] == "research"
