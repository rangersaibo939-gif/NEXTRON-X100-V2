#!/data/data/com.termux/files/usr/bin/bash
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT" || exit 1
LOG="$ROOT/.nextron-fast.log"
APK_DIR="$ROOT/.nextron-build-output"
mkdir -p "$APK_DIR"
exec > >(tee -a "$LOG") 2>&1

echo "=== NEXTRON FAST BUILD $(date) ==="
echo "ROOT: $ROOT"
echo "BRANCH: $(git branch --show-current)"

echo "--- TESTS ---"
python -m pytest -q || { echo "TESTS FAILED"; exit 2; }

echo "--- SDK CHECK ---"
python - <<'PY'
from core.app_builder.doctor import ToolchainDoctor
for x in ToolchainDoctor().check():
    print(f"{x.name}: {'OK' if x.available else 'MISSING'} {x.path or ''}")
PY

echo "--- BUILDER IMPORT CHECK ---"
python - <<'PY'
from core.app_builder import AppBuildPipeline, BuildRequest
from core.app_builder.project_generator import AndroidProjectGenerator
from core.app_builder.toolchain import ToolchainRegistry
print('Builder imports: OK')
print('Project generator: OK')
print('Toolchain registry: OK')
PY

echo "--- NEXT ACTION ---"
echo "Environment and Builder V2 smoke checks completed."
echo "Full APK build will run only when Android SDK tools are available."
echo "Log: $LOG"
echo "APK output directory: $APK_DIR"
