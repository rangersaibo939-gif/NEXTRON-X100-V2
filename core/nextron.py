from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from core.ai_planner import AIPlanner
from core.app_builder.contracts import BuildRequest
from core.app_builder.pipeline import AppBuildPipeline
from core.app_builder.project_generator import AndroidProjectGenerator
from core.app_builder.toolchain.gradle_backend import GradleAndroidAdapter
from core.multi_brain import MultiBrainOrchestrator
from core.providers.catalog import build_providers


def _copy_apk_to_downloads(apk: Path, app_name: str) -> Path | None:
    downloads = Path("/storage/emulated/0/Download")
    try:
        downloads.mkdir(parents=True, exist_ok=True)
        safe_app_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in app_name).strip() or "NEXTRON_App"
        destination = downloads / f"{safe_app_name}.apk"
        shutil.copy2(apk, destination)
        return destination
    except (OSError, PermissionError):
        return None


def _android_shell(*args: str) -> tuple[int, str]:
    try:
        proc = subprocess.run(list(args), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
        return proc.returncode, proc.stdout.strip()
    except OSError as exc:
        return 127, str(exc)


def _install_and_smoke_test(apk: Path, package_name: str, project_dir: Path) -> bool:
    if os.environ.get("NEXTRON_AUTO_INSTALL", "1").lower() in {"0", "false", "no"}:
        return False
    if not Path("/data/data/com.termux").exists():
        return False

    install_path = Path("/storage/emulated/0/Download/.nextron-install.apk")
    runtime_log = project_dir / "nextron-runtime.log"
    try:
        install_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(apk, install_path)
    except OSError as exc:
        runtime_log.write_text(f"INSTALL COPY FAILED: {exc}\n", encoding="utf-8")
        return False

    install_rc, install_out = _android_shell("cmd", "package", "install", "-r", str(install_path))
    launch_rc, launch_out = 1, ""
    if install_rc == 0:
        launch_rc, launch_out = _android_shell("am", "start", "-S", "-W", "-n", f"{package_name}/.MainActivity")
    log_rc, log_out = _android_shell("logcat", "-d", "-v", "threadtime", "-t", "5000")
    runtime_log.write_text(
        "===== NEXTRON AUTOMATIC ANDROID SMOKE TEST =====\n"
        f"APK: {apk}\nPACKAGE: {package_name}\n\n"
        f"===== INSTALL rc={install_rc} =====\n{install_out}\n\n"
        f"===== LAUNCH rc={launch_rc} =====\n{launch_out}\n\n"
        f"===== LOGCAT rc={log_rc} =====\n{log_out}\n",
        encoding="utf-8",
    )
    return install_rc == 0 and launch_rc == 0


def _multi_brain_context(task: str, providers: dict) -> str:
    """Ask specialist brains first, then pass their consensus to the app planner."""
    orchestrator = MultiBrainOrchestrator(providers)
    result = orchestrator.run(task)
    print("Multi-Brain: specialist consensus ready")
    for item in result.results:
        status = "OK" if item.success else f"FAILED: {item.error}"
        print(f"  {item.role}: {status} ({item.provider}/{item.model})")
    print("Multi-Brain consensus:")
    print(result.consensus)
    return result.consensus


def main(request: str) -> int:
    request = request.strip()
    if not request:
        print("ERROR: empty app request")
        return 2

    providers = build_providers()
    provider = providers.get("reasoner") or providers.get("openrouter") or providers.get("groq")
    if provider is None and providers:
        provider = next(iter(providers.values()))
    if provider is None:
        print("ERROR: no AI provider configured")
        return 2

    print("NEXTRON X-100")
    print("==============================")
    print("Stage 1/4: Multi-Brain planning...")

    try:
        planned_request = _multi_brain_context(request, providers)
        plan = AIPlanner(provider).plan(planned_request)
    except Exception as exc:
        print(f"FAILED [multi-brain planning]: {exc}")
        return 1

    print("Plan: VALID")
    print(f"App: {plan.app_name}")
    print(f"Package: {plan.package_name}")
    print(f"Screens: {', '.join(plan.screens)}")
    print(f"Features: {', '.join(plan.features)}")
    print(f"Actions: {', '.join(plan.actions)}")
    print(f"Data model fields: {len(plan.data_model)}")

    print("Stage 2/4: Kotlin/Compose generation...")
    output_root = Path.cwd() / ".nextron-build-output"
    project_dir = output_root / plan.package_name.replace(".", "_")
    output_root.mkdir(parents=True, exist_ok=True)

    try:
        generated = AndroidProjectGenerator().generate(
            str(project_dir), plan.package_name, plan.app_name,
            description=plan.description, screens=plan.screens, features=plan.features,
            actions=plan.actions, theme=plan.theme, data_model=plan.data_model,
        )
    except Exception as exc:
        print(f"FAILED [generation]: {exc}")
        return 1

    print(f"Project: {generated.root}")
    print("Stage 3/4: Gradle Android build...")
    request_obj = BuildRequest(
        project_id=plan.package_name, project_name=plan.app_name, package_name=plan.package_name,
        working_directory=str(generated.root), target_sdk=36, min_sdk=26, build_type="debug",
    )

    try:
        result = AppBuildPipeline(adapter=GradleAndroidAdapter(), max_repairs=0).build(request_obj)
    except Exception as exc:
        print(f"FAILED [gradle]: {exc}")
        return 1

    if result.status.value != "success":
        print("BUILD FAILED")
        print(f"Failed stage: {result.failed_stage.value if result.failed_stage else 'unknown'}")
        print(f"Error: {result.error_message}")
        return 1
    if not result.artifacts:
        print("FAILED: Gradle returned no APK")
        return 1

    print("BUILD SUCCESS")
    apk = Path(result.artifacts[0].path).resolve()
    print("Stage 4/4: APK verification...")
    if not apk.is_file() or apk.stat().st_size <= 0:
        print(f"FAILED: invalid APK artifact: {apk}")
        return 1

    print(f"APK: {apk}")
    print(f"APK SIZE: {apk.stat().st_size} bytes")
    destination = _copy_apk_to_downloads(apk, plan.app_name)
    if destination:
        print(f"DOWNLOAD APK: {destination}")

    if _install_and_smoke_test(apk, plan.package_name, generated.root):
        print("ANDROID INSTALL: SUCCESS")
        print("ANDROID LAUNCH: SUCCESS")
    else:
        print("ANDROID INSTALL/LAUNCH: NOT CONFIRMED")
    print(f"RUNTIME LOG: {generated.root / 'nextron-runtime.log'}")
    print("==============================")
    print("NEXTRON BUILD COMPLETE")
    return 0


if __name__ == "__main__":
    request = " ".join(sys.argv[1:]).strip()
    if not request:
        request = "Build a simple expense tracker with a dark UI, an add expense button, categories and monthly total."
    raise SystemExit(main(request))
