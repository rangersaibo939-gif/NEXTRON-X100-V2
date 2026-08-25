from pathlib import Path
import sys

# When this file is executed directly (python tools/build_nextron_app.py),
# Python puts tools/ on sys.path rather than the repository root.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.app_builder.project_generator import AndroidProjectGenerator
from tools.interactive_console import make_interactive
from tools.dashboard_scroll_fix import fix_generated_dashboard

APP_NAME = "NEXTRON X-100"
PACKAGE = "com.nextron.x100"


def build_project(output: str) -> Path:
    root = Path(output)
    AndroidProjectGenerator().generate(
        str(root),
        PACKAGE,
        APP_NAME,
        description="AI-powered multi-brain app builder and autonomous build console.",
        screens=("Multi-Brain Dashboard", "Agent Tasks", "Build Status", "App History", "Settings"),
        features=("Multi-Brain orchestration", "Autonomous coding", "Build monitoring", "APK delivery"),
        theme={"mode": "dark"},
        data_model={"activeTask": "string", "buildStatus": "string", "artifactPath": "string"},
        actions=("Create App", "Run Agent", "Build APK", "Download APK"),
    )
    fix_generated_dashboard(str(root))
    make_interactive(str(root))
    return root


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate the NEXTRON X-100 Android app")
    parser.add_argument("output", help="Directory for the generated Android project")
    args = parser.parse_args()
    print(f"Generating {APP_NAME} in {args.output}")
    print(build_project(args.output))
