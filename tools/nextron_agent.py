#!/usr/bin/env python3
"""Autonomous NEXTRON V2 coding loop.

The workflow gives this agent a repository snapshot and the latest validation
output. The model proposes a unified diff; the runner applies it, validates it,
and repeats until the V2 acceptance checks pass or the iteration budget ends.
"""
from __future__ import annotations

import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

API = "https://openrouter.ai/api/v1/chat/completions"
MODEL = os.getenv("NEXTRON_AGENT_MODEL", "openrouter/auto")
MAX_ITERATIONS = int(os.getenv("NEXTRON_AGENT_MAX_ITERATIONS", "5"))
ROOT = Path.cwd()

EXCLUDE_PARTS = {".git", ".venv", "__pycache__", ".nextron-build-output", ".nextron-generator-test", "build", ".gradle"}
EXTENSIONS = {".py", ".md", ".yml", ".yaml", ".kts", ".properties", ".json", ".toml"}


def run(cmd: list[str], timeout: int = 300) -> tuple[int, str]:
    proc = subprocess.run(cmd, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    return proc.returncode, proc.stdout[-30000:]


def snapshot() -> str:
    parts: list[str] = []
    rc, status = run(["git", "status", "--short"])
    parts.append("===== GIT STATUS =====\n" + status)
    rc, diff = run(["git", "diff", "--", "."])
    parts.append("===== CURRENT DIFF =====\n" + diff[-50000:])

    files: list[Path] = []
    for p in ROOT.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in EXTENSIONS:
            continue
        if any(part in EXCLUDE_PARTS for part in p.relative_to(ROOT).parts):
            continue
        files.append(p)
    files.sort()

    total = 0
    for p in files:
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            continue
        if len(text) > 30000:
            text = text[:30000] + "\n...[truncated]..."
        block = f"===== FILE: {p.relative_to(ROOT)} =====\n{text}\n"
        if total + len(block) > 110000:
            break
        parts.append(block)
        total += len(block)
    return "\n".join(parts)


def validate() -> tuple[bool, str]:
    checks = [
        ([sys.executable, "-m", "py_compile", "core/nextron.py", "core/app_plan.py", "core/ai_planner.py"], 120),
        ([sys.executable, "-m", "pytest", "-q"], 300),
    ]
    output: list[str] = []
    for cmd, timeout in checks:
        rc, text = run(cmd, timeout)
        output.append("$ " + " ".join(cmd) + "\n" + text)
        if rc != 0:
            return False, "\n\n".join(output)

    # Exercise the actual Android generator and Gradle toolchain without
    # depending on the local Termux environment.
    generator = """
from pathlib import Path
from core.app_builder.project_generator import AndroidProjectGenerator
root = Path('/tmp/nextron-agent-android')
import shutil
if root.exists(): shutil.rmtree(root)
AndroidProjectGenerator().generate(
    str(root), 'com.nextron.autotest', 'NEXTRON Agent Test',
    screens=('Home', 'Add Item'),
    features=('Dark mode', 'Totals'),
    actions=('Add Item', 'Delete Item'),
)
print(root)
"""
    rc, text = run([sys.executable, "-c", generator], 120)
    output.append("$ generator smoke test\n" + text)
    if rc != 0:
        return False, "\n\n".join(output)

    rc, text = run(["gradle", "-p", "/tmp/nextron-agent-android", ":app:assembleDebug", "--no-daemon"], 420)
    output.append("$ gradle -p /tmp/nextron-agent-android :app:assembleDebug --no-daemon\n" + text)
    return rc == 0, "\n\n".join(output)


def ask_model(context: str, validation: str, iteration: int) -> str:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY is missing")

    system = """You are the autonomous senior engineer for NEXTRON X-100 V2.
Work directly on the repository snapshot supplied by the runner.
Goal: finish NEXTRON V2, not merely make the current test green.

Hard requirements:
- Android output is Kotlin + Jetpack Compose; do not introduce Java or XML layouts.
- Preserve working architecture and existing tests unless a change is required.
- Fix root causes, not symptoms.
- Do not add fake/demo success paths or hard-coded claims.
- Do not modify secrets, credentials, workflow permissions, or unrelated files.
- Prefer small, production-quality changes.
- The repository must remain buildable after every iteration.

Your response MUST be exactly one of these forms:
1) DONE\n when the V2 acceptance criteria are genuinely satisfied.
2) PATCH\n<unified git diff>\nENDPATCH\n
The patch must be directly applicable with `git apply` from the repository root.
Do not use markdown fences around the patch. Do not explain outside the required markers.
"""
    user = f"""Iteration {iteration}/{MAX_ITERATIONS}.

===== VALIDATION RESULT =====
{validation}

===== REPOSITORY SNAPSHOT =====
{context}

===== V2 ACCEPTANCE TARGET =====
- AI request -> validated AppPlan -> Kotlin/Compose project generation -> Gradle APK build is one reliable pipeline.
- Generated projects reflect the AI plan's screens, features, theme, data model and actions instead of only a counter/demo.
- Build results identify the failed stage and artifact reliably.
- APK output can be surfaced/copied for the user.
- Existing Python tests pass and important new behavior has tests.
- The implementation is robust enough to continue from GitHub Actions without the user staying in chat.

Inspect the code and validation output. Implement the highest-value missing piece now.
"""
    body = {"model": MODEL, "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}], "temperature": 0.1, "max_tokens": 12000}
    import json
    request = urllib.request.Request(API, data=json.dumps(body).encode(), headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json", "X-Title": "NEXTRON V2 Autonomous Builder"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            payload = json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        raise RuntimeError(f"OpenRouter HTTP {exc.code}: {detail[:2000]}") from exc
    text = payload["choices"][0]["message"]["content"].strip()
    return text


def apply_response(response: str) -> bool:
    if response.strip() == "DONE":
        print("AUTONOMOUS AGENT: DONE")
        return False
    if not response.startswith("PATCH\n") or "\nENDPATCH" not in response:
        raise RuntimeError("Agent returned neither DONE nor a valid PATCH response")
    patch = response[len("PATCH\n"):response.rfind("\nENDPATCH")]
    patch_path = ROOT / ".nextron-agent.patch"
    patch_path.write_text(patch, encoding="utf-8")
    try:
        rc, out = run(["git", "apply", "--whitespace=fix", str(patch_path)], 120)
    finally:
        patch_path.unlink(missing_ok=True)
    if rc != 0:
        print(out)
        raise RuntimeError("Agent patch could not be applied")
    return True


def main() -> int:
    print(f"NEXTRON autonomous loop: model={MODEL}, iterations={MAX_ITERATIONS}")
    last_validation = "No validation has been run yet."
    for iteration in range(1, MAX_ITERATIONS + 1):
        print(f"===== AUTONOMOUS ITERATION {iteration}/{MAX_ITERATIONS} =====")
        ok, validation = validate()
        print(validation)
        if ok:
            last_validation = validation + "\nAll validation checks currently pass; inspect acceptance target for missing product behavior."
        else:
            last_validation = validation

        try:
            response = ask_model(snapshot(), last_validation, iteration)
        except Exception as exc:
            print(f"AUTONOMOUS AGENT: Model API call failed: {exc}")
            if ok:
                print("AUTONOMOUS AGENT: Validation checks are currently green; exiting autonomous loop cleanly.")
                return 0
            raise
        if not apply_response(response):
            return 0

    ok, validation = validate()
    print("===== FINAL VALIDATION =====")
    print(validation)
    if not ok:
        print("AUTONOMOUS AGENT: iteration budget exhausted with failing validation")
        return 1
    print("AUTONOMOUS AGENT: validation green; changes are ready for commit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
