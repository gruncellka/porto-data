# Porto Data Bugbot Rules

## Scope

- This file defines repository-level review rules for Bugbot in `porto-data`.
- Keep findings focused on data integrity, validation correctness, and release safety.
- Align checks with `.cursorrules` for this repository.
- Treat `porto-data` as an independent package with its own responsibility and review boundaries.
- Review scope is only changes inside this `porto-data` repository.
- Do not raise findings for files, workflows, or policies in other repositories of this workspace.

## Rule format

- Use explicit, actionable findings.
- Use blocking bugs for correctness, safety, or release risks.
- Use non-blocking bugs for maintainability and coordination risks.

## Rules

### 1) Data or schema changes must have validation-facing test updates (blocking)

If a PR changes files in `porto_data/data/**`, `porto_data/schemas/**`, `scripts/**`, or `cli/**` and has no changes in `tests/**`, then:

- Add a blocking Bug titled `Core data or validation logic changed without tests`.
- Body: `This change affects data, schema, or validation behavior but does not update tests. Add or update focused tests in tests/.`
- Apply labels `quality`, `tests`.

### 2) Manual edits to metadata are not allowed (blocking)

If a PR directly edits `porto_data/metadata.json` while no related changes exist in data/schema/mappings or metadata generation paths (`porto_data/data/**`, `porto_data/schemas/**`, `porto_data/mappings.json`, `scripts/generate_metadata.py`, `cli/commands/metadata.py`), then:

- Add a blocking Bug titled `metadata.json appears manually edited`.
- Body: `metadata.json is generated output and should not be hand-edited. Regenerate it from source changes instead.`
- Apply labels `reliability`, `release`.

### 3) Data/schema/mapping changes must include regenerated metadata (blocking)

If a PR changes any of `porto_data/data/**`, `porto_data/schemas/**`, or `porto_data/mappings.json` and does not also change `porto_data/metadata.json`, then:

- Add a blocking Bug titled `Data or schema changed without metadata refresh`.
- Body: `Changes to data/schema/mappings require regenerated porto_data/metadata.json in the same PR.`
- Apply labels `quality`, `release`.

### 4) New subprocess.run calls need explicit failure handling (blocking)

For new `subprocess.run(...)` calls in `scripts/**/*.py` or `cli/**/*.py`, require either:

- `check=True`, or
- explicit non-zero `returncode` handling.

If neither exists:

- Add a blocking Bug titled `subprocess.run without clear error handling`.
- Body: `New subprocess invocation can fail silently. Use check=True or explicit returncode handling with clear behavior.`
- Apply labels `reliability`, `python`.

### 5) Python import hacks should not be introduced (blocking)

If a PR adds `sys.path` manipulation (for example `sys.path.append(...)`) in `scripts/**` or `cli/**`, then:

- Add a blocking Bug titled `sys.path import hack introduced`.
- Body: `Use package-style imports and project structure conventions instead of sys.path mutation.`
- Apply labels `python`, `maintainability`.

### 6) JSON formatting and key-order drift should be flagged (non-blocking)

If changed JSON files under `porto_data/**` appear minified, use non-4-space indentation, or show obvious key reordering unrelated to behavior, then:

- Add a non-blocking Bug titled `JSON formatting or key-order drift`.
- Body: `Preserve JSON readability and key order. Reformat consistently and avoid unnecessary key reshuffling.`
- Apply label `maintainability`.

### 7) Changelog should accompany user-visible data behavior changes (non-blocking)

If a PR changes published data or schema contracts (`porto_data/data/**`, `porto_data/schemas/**`, `porto_data/mappings.json`) and does not update `CHANGELOG.md`, then:

- Add a non-blocking Bug titled `User-visible data change without changelog update`.
- Body: `Consider documenting this data/schema behavior change in CHANGELOG.md for consumers.`
- Apply label `release-notes`.

### 8) TODO/FIXME comments must be tracked (non-blocking)

If changed code includes `TODO` or `FIXME` without an issue reference like `#123` or `ABC-123`, then:

- Add a non-blocking Bug titled `Untracked TODO/FIXME comment`.
- Body: `Link TODO/FIXME to a tracked issue (for example TODO(#123): ...) or remove it.`
- Apply label `maintainability`.
