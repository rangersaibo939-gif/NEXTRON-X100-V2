from core.self_improvement import SelfImprovementLoop


def test_inspect_finds_first_missing_capability():
    loop = SelfImprovementLoop(capabilities=("multi-brain orchestration", "APK delivery"))
    assert loop.inspect(("multi-brain orchestration", "autonomous coding", "APK delivery")) == ("autonomous coding",)


def test_plan_next_creates_development_task():
    loop = SelfImprovementLoop(capabilities=("multi-brain orchestration",))
    task = loop.plan_next(("multi-brain orchestration", "autonomous coding"))
    assert task is not None
    assert task.capability == "autonomous coding"
    assert loop.history[-1] == task


def test_run_agent_without_provider_is_still_planned():
    loop = SelfImprovementLoop(capabilities=())
    task = loop.create_task("autonomous coding")
    result = loop.run_agent(task)
    assert result.status == "planned"
    assert result.task == task
