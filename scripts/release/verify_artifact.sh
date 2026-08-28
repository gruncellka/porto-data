#!/usr/bin/env bash
# Build once (npm tarball + PyPI sdist/wheel), verify, clean-env smoke.
# Leaves gruncellka-porto-data-*.tgz and dist/ for publish upload.
# Run: ./scripts/release/verify_artifact.sh or make artifact
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

if [ -f venv/bin/activate ]; then
    # shellcheck source=/dev/null
    . venv/bin/activate
elif [ -f .venv/bin/activate ]; then
    # shellcheck source=/dev/null
    . .venv/bin/activate
fi

rm -f gruncellka-porto-data-*.tgz
rm -rf dist artifact-smoke-npm artifact-smoke-pypi dist-test build *.egg-info

echo "=== Build npm tarball ==="
npm pack --silent
TARBALL="$(ls -t gruncellka-porto-data-*.tgz 2>/dev/null | head -1)"
test -n "$TARBALL" || { echo "No tarball produced"; exit 1; }
echo "Tarball: $TARBALL"

echo "=== npm package contract ==="
LIST="$(tar -tzf "$TARBALL")"
echo "$LIST" | grep -q 'package/porto_data/providers/' || {
    echo "FAIL: missing package/porto_data/providers/"
    exit 1
}
echo "$LIST" | grep -q 'package/porto_data/policy/' || {
    echo "FAIL: missing package/porto_data/policy/"
    exit 1
}
echo "$LIST" | grep -q 'package/porto_data/schemas/kinds.schema.json' || {
    echo "FAIL: missing kinds.schema.json"
    exit 1
}
if echo "$LIST" | grep -qE 'package/(docs|tests|\.github|\.cursor)/'; then
    echo "FAIL: forbidden path in npm package"
    echo "$LIST" | grep -E 'package/(docs|tests|\.github|\.cursor)/' || true
    exit 1
fi
echo "npm tarball structure OK"

echo "=== npm clean-env smoke ==="
TESTDIR="${ROOT}/artifact-smoke-npm"
rm -rf "$TESTDIR"
mkdir -p "$TESTDIR"
cd "$TESTDIR"
npm init -y >/dev/null
npm install --silent "${ROOT}/${TARBALL}"
node -e "
const pkg = require('@gruncellka/porto-data');
const fs = require('fs');
const path = require('path');
const root = path.join(process.cwd(), 'node_modules/@gruncellka/porto-data');
const pdir = path.join(root, 'porto_data');
const files = fs.readdirSync(pdir);
const hasPy = files.some(f => f.endsWith('.py'));
if (hasPy) { console.error('FAIL: .py file in npm package'); process.exit(1); }
if (!fs.existsSync(path.join(root, 'porto_data/schemas/kinds.schema.json'))) {
  console.error('FAIL: missing kinds.schema.json');
  process.exit(1);
}
if (fs.existsSync(path.join(root, 'docs'))) {
  console.error('FAIL: docs/ must not be shipped');
  process.exit(1);
}
if (!pkg.policy || !pkg.providers || pkg.global) {
  console.error('FAIL: metadata shape (expected policy/providers, not global)');
  process.exit(1);
}
console.log('require() OK, project.version:', pkg.project?.version);
"
cd "$ROOT"
rm -rf "$TESTDIR"
echo "npm smoke OK (tarball kept: $TARBALL)"

echo ""
echo "=== Build PyPI sdist + wheel ==="
python3 -m pip install -q build
python3 -m build
WHEEL="$(ls -t dist/gruncellka_porto_data-*.whl 2>/dev/null | head -1)"
SDIST="$(ls -t dist/gruncellka_porto_data-*.tar.gz 2>/dev/null | head -1)"
test -n "$WHEEL" || { echo "no wheel in dist/"; exit 1; }
test -n "$SDIST" || { echo "no sdist in dist/"; exit 1; }
echo "Wheel: $WHEEL"
echo "Sdist: $SDIST"

echo "=== wheel contract ==="
WHEEL_LIST="$(python3 -m zipfile -l "$WHEEL")"
echo "$WHEEL_LIST" | grep -q 'porto_data/' || {
    echo "FAIL: porto_data/ missing from wheel"
    exit 1
}
if echo "$WHEEL_LIST" | grep -qE '(^| )(tests|docs|\.github|\.cursor)/'; then
    echo "FAIL: forbidden path in wheel"
    exit 1
fi
echo "wheel structure OK"

echo "=== PyPI clean-env smoke ==="
PYDIR="${ROOT}/artifact-smoke-pypi"
rm -rf "$PYDIR" && mkdir -p "$PYDIR"
python3 -m pip install -q --force-reinstall "$WHEEL"
cd "$PYDIR"
python3 -c "
from porto_data import __version__, metadata, get_package_root
root = get_package_root()
assert __version__, 'missing __version__'
assert 'project' in metadata, 'missing metadata.project'
assert 'policy' in metadata and 'formats' in metadata, 'missing policy/formats'
assert 'global' not in metadata, 'stale global key in metadata'
assert (root / 'schemas' / 'kinds.schema.json').is_file(), 'missing kinds.schema.json'
assert root.exists(), 'get_package_root() failed'
print('__version__:', __version__)
"
cd "$ROOT"
rm -rf "$PYDIR"
echo "PyPI smoke OK (dist/ kept)"

echo ""
echo "Artifact verification passed."
