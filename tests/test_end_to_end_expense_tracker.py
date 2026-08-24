from pathlib import Path

from core.app_builder.project_generator import AndroidProjectGenerator


def test_expense_tracker_plan_generates_compose_project(tmp_path: Path):
    output = tmp_path / "expense-tracker"
    AndroidProjectGenerator().generate(
        str(output),
        "com.nextron.expensetracker",
        "Expense Tracker",
        screens=("Dashboard", "Add Expense", "Expense History"),
        features=("Monthly totals", "Category breakdown", "Offline storage"),
        actions=("Add Expense", "Delete Expense", "Filter by category"),
    )

    assert (output / "app" / "src" / "main" / "AndroidManifest.xml").exists()
    assert (output / "app" / "src" / "main" / "java" / "com" / "nextron" / "expensetracker" / "MainActivity.kt").exists()
    assert (output / "settings.gradle.kts").exists()

    source = (output / "app" / "src" / "main" / "java" / "com" / "nextron" / "expensetracker" / "MainActivity.kt").read_text()
    assert "Dashboard" in source
    assert "Add Expense" in source
    assert "Expense History" in source
    assert "Monthly totals" in source
    assert "Category breakdown" in source
