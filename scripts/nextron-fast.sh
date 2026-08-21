#!/data/data/com.termux/files/usr/bin/bash
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

export ANDROID_SDK_ROOT="${ANDROID_SDK_ROOT:-$PREFIX/lib/android-sdk}"
export ANDROID_HOME="${ANDROID_HOME:-$ANDROID_SDK_ROOT}"

echo "--- TESTS ---"
python -m pytest -q || {
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
    raise SystemExit(4)

if not result.artifacts:
    print("BUILD ERROR: no APK artifact returned")
    raise SystemExit(5)

apk = Path(result.artifacts[0].path)

if not apk.is_file():
    print(f"BUILD ERROR: APK does not exist: {apk}")
    raise SystemExit(6)

print(f"APK: {apk}")

output = Path.home() / "NEXTRON-X100-V2" / ".nextron-build-output"
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

"$ANDROID_SDK_ROOT/build-tools/36.0.0/apksigner" verify --verbose "$APK"

echo "--- BUILD COMPLETE ---"
ls -lh "$APK"

echo "APK: $APK"
echo "Log: $LOG"
