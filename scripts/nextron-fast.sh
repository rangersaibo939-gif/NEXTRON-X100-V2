#!/usr/bin/env bash
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1

LOG="$ROOT/.nextron-fast.log"
APK_DIR="$ROOT/.nextron-build-output"
SMOKE_DIR="$HOME/nextron-apk-smoke"

mkdir -p "$APK_DIR"
exec > >(tee -a "$LOG") 2>&1

echo "=== NEXTRON FAST BUILD $(date) ==="
echo "ROOT: $ROOT"
echo "BRANCH: $(git branch --show-current)"

PREFIX="${PREFIX:-/usr}"
DEFAULT_SDK="/opt/android-sdk"
if [ ! -d "$DEFAULT_SDK" ]; then
    DEFAULT_SDK="$PREFIX/lib/android-sdk"
fi
export ANDROID_SDK_ROOT="${ANDROID_SDK_ROOT:-${ANDROID_HOME:-$DEFAULT_SDK}}"
export ANDROID_HOME="${ANDROID_HOME:-$ANDROID_SDK_ROOT}"

echo "--- TESTS ---"
PYTHONPATH=. pytest -q || python3 -m pytest -q || {
    echo "TESTS FAILED"
    exit 2
}

echo "--- SDK CHECK ---"
python - <<'PY'
from core.app_builder.doctor import ToolchainDoctor

failed = False
for x in ToolchainDoctor().check():
    status = "OK" if x.available else "MISSING"
    print(f"{x.name}: {status} {x.path or ''}")
    if not x.available:
        failed = True

if failed:
    raise SystemExit(3)
PY

echo "--- BUILDER IMPORT CHECK ---"
python - <<'PY'
from core.app_builder import AppBuildPipeline, BuildRequest
from core.app_builder.project_generator import AndroidProjectGenerator
from core.app_builder.toolchain import ToolchainRegistry
from core.app_builder.toolchain.gradle_backend import GradleAndroidAdapter
from core.builder import android_app_spec, ProjectBuilder

print("Builder imports: OK")
print("Project generator: OK")
print("Toolchain registry: OK")
print("Gradle adapter: OK")
print("Compose generator: OK")
PY

echo "--- GENERATE PROJECT ---"
rm -rf "$SMOKE_DIR"

python - <<'PY'
from pathlib import Path
from core.builder import android_app_spec, ProjectBuilder

spec = android_app_spec(
    "NEXTRONSmoke",
    "com.nextron.smoketest",
    "NEXTRON Builder V2 APK smoke test",
)

root = ProjectBuilder().build(
    spec,
    Path.home() / "nextron-apk-smoke",
)

print(f"PROJECT: {root}")
PY

echo "--- GRADLE BUILD ---"

python - <<'PY'
import sys
from pathlib import Path
from core.app_builder import AppBuildPipeline, BuildRequest
from core.app_builder.toolchain.gradle_backend import GradleAndroidAdapter

project = Path.home() / "nextron-apk-smoke"

request = BuildRequest(
    project_id="nextron-smoke",
    project_name="NEXTRONSmoke",
    package_name="com.nextron.smoketest",
    working_directory=str(project),
    build_type="debug",
)

pipeline = AppBuildPipeline(
    adapter=GradleAndroidAdapter(),
    max_repairs=0,
)

result = pipeline.build(request)

print(f"BUILD STATUS: {result.status.value}")

for log in result.logs:
    if log.level == "ERROR":
        print(f"[ERROR] {log.stage.value}: {log.message}")

if result.status.value != "success":
    print(f"BUILD ERROR: {result.error_message}")
    sys.exit(4)

if not result.artifacts:
    print("BUILD ERROR: no APK artifact returned")
    sys.exit(5)

apk = Path(result.artifacts[0].path)

if not apk.is_file():
    print(f"BUILD ERROR: APK does not exist: {apk}")
    sys.exit(6)

print(f"APK: {apk}")

output = Path.cwd() / ".nextron-build-output"
output.mkdir(parents=True, exist_ok=True)

destination = output / "nextron-smoke-debug.apk"
destination.write_bytes(apk.read_bytes())

print(f"OUTPUT: {destination}")
print(f"SIZE: {destination.stat().st_size} bytes")
PY

echo "--- APK VERIFY ---"

APK="$APK_DIR/nextron-smoke-debug.apk"

if [ ! -f "$APK" ]; then
    echo "APK NOT FOUND: $APK"
    exit 7
fi

APKSIGNER="$(find "$ANDROID_SDK_ROOT/build-tools" -name apksigner | sort -V | tail -n 1)"
if [ -z "$APKSIGNER" ] || [ ! -f "$APKSIGNER" ]; then
    APKSIGNER="$(which apksigner 2>/dev/null || true)"
fi

if [ -n "$APKSIGNER" ] && [ -f "$APKSIGNER" ]; then
    "$APKSIGNER" verify --verbose "$APK"
else
    echo "apksigner not found, skipping signature verification"
fi

echo "--- BUILD COMPLETE ---"
ls -lh "$APK"

echo "APK: $APK"
echo "Log: $LOG"
