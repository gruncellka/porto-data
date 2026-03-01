#!/usr/bin/env bash
# Test npm and PyPI packages before publishing.
# Run from repo root: ./tests/test_publish.sh or make test-publish.
# Used in .github/workflows/publish.yml validate job to reject publish if this fails.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# Use venv if present (local), else current python/pip (CI)
if [ -f venv/bin/activate ]; then
    . venv/bin/activate
fi

echo "=== Testing NPM package ==="
npm pack --silent
TARBALL="$(ls -t gruncellka-porto-data-*.tgz 2>/dev/null | head -1)"
test -n "$TARBALL" || { echo "No tarball produced"; exit 1; }
TESTDIR="${ROOT}/test-publish-npm"
rm -rf "$TESTDIR"
mkdir -p "$TESTDIR"
cd "$TESTDIR"
npm init -y >/dev/null
npm install --silent "${ROOT}/${TARBALL}"
node -e "
const pkg = require('@gruncellka/porto-data');
const fs = require('fs');
const path = require('path');
const pdir = path.join(process.cwd(), 'node_modules/@gruncellka/porto-data/porto_data');
const files = fs.readdirSync(pdir);
const hasPy = files.some(f => f.endsWith('.py'));
if (hasPy) { console.error('FAIL: .py file in npm package'); process.exit(1); }
console.log('✓ require() OK, project.version:', pkg.project?.version);
console.log('✓ No Python files in porto_data/');
"
cd "$ROOT"
rm -f "$TARBALL"
echo "✓ NPM package test passed"

echo ""
echo "=== Testing PyPI wheel ==="
python3 -m pip install -q build 2>/dev/null || true
rm -rf dist-test && mkdir -p dist-test
python3 -m build --wheel --outdir dist-test 2>/dev/null
python3 -m pip install -q --force-reinstall dist-test/gruncellka_porto_data-*.whl
# Run import test from an empty dir so Python uses the installed wheel, not local porto_data/
PYDIR="${ROOT}/test-publish-pypi"
rm -rf "$PYDIR" && mkdir -p "$PYDIR"
cd "$PYDIR"
python3 -c "
from porto_data import __version__, metadata, get_package_root
assert __version__, 'missing __version__'
assert 'project' in metadata, 'missing metadata.project'
assert get_package_root().exists(), 'get_package_root() failed'
print('✓ __version__:', __version__)
print('✓ metadata, get_package_root() OK')
"
cd "$ROOT"
echo "✓ PyPI package test passed"
echo ""
echo "All publish tests passed."
