from nextron import AIModel, register_model, classify_task, choose_model


def setup_models():
    register_model(
        AIModel(
            name="Coding Specialist",
            provider="test",
            coding=95,
            reasoning=80,
            reliability=90,
            speed=80,
        )
    )

    register_model(
        AIModel(
            name="Research Specialist",
            provider="test",
            research=95,
            reasoning=90,
            reliability=92,
            speed=75,
        )
    )


def test_task_classification():
    assert classify_task("Debug my Android Kotlin build") == "coding"
    assert classify_task("Research the latest AI models") == "research"


def test_model_selection():
    setup_models()

    selected = choose_model("Debug my Android Kotlin build")

    assert selected is not None
    assert selected.name == "Coding Specialist"