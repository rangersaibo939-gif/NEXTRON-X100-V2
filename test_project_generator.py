import json
from pathlib import Path

from core.app_builder.project_generator import AndroidProjectGenerator


def test_generator_materializes_plan_and_compose_project(tmp_path: Path):
    root = tmp_path / "generated"
    AndroidProjectGenerator().generate(
        str(root),
        "com.nextron.expenses",
        "Expense Tracker",
        description="Track monthly spending",
        screens=("Home", "Add Expense"),
        features=("Monthly totals", "Categories"),
        actions=("Add Expense", "Delete Expense"),
        theme={"mode": "dark"},
        data_model={"expense": "amount, category, date", "currency": "INR"},
    )

    build_file = (root / "build.gradle.kts").read_text()
    activity = (root / "app/src/main/java/com/nextron/expenses/MainActivity.kt").read_text()
    plan = json.loads((root / "app/src/main/assets/nextron_plan.json").read_text())

    assert 'id("com.android.application") version "8.5.2"' in build_file
    assert 'id("org.jetbrains.kotlin.plugin.compose") version "2.0.21"' in build_file
    assert "Expense Tracker" in activity
    assert "Add Expense" in activity
    assert "Monthly totals" in activity
    assert "amount, category, date" in activity
    assert "darkColorScheme()" in activity
    assert plan["data_model"]["currency"] == "INR"
    assert plan["screens"] == ["Home", "Add Expense"]
