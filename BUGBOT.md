# Porto Data Bugbot Rules

## Scope

- Review rules for Bugbot in this `porto-data` tree only: data integrity, validation correctness, release safety.
- **Consistency** means cross-file agreement: registry ↔ mappings ↔ disk, catalog JSON ↔ **`graph.json`**, units, services ↔ prices ↔ graph.
- **Resolution** (for SDKs/loaders) is anchored in each provider’s **`graph.json`**: **`dependencies`**, **`edges`** (product × zones × weight tiers), **`services`**, plus schema **`porto_data/schemas/graph.schema.json`**. Price lookup uses **`dependencies`** paths and price-schema join keys (`product_id`, `zone`, `weight_tier` / `service_id`). Loaders must not assume removed layouts (`porto_data/data/`, `data_links.json`, top-level **`links`**, **`lookup_rules`**, **`global_settings`**, or **`price_lookup`** on the graph).
- Align with `.cursorrules` and `CONTRIBUTING.md`.
- Do not flag files, workflows, or policies outside this repository.

## Severity

- **Blocking:** correctness, safety, or release risk.
- **Non-blocking:** maintainability, coordination, or “verify before merge” resolution risk.

## Rules

### 1) Data or schema changes need test updates (blocking)

If a PR changes `porto_data/policy/**`, `porto_data/formats/**`, `porto_data/providers/**`, `porto_data/schemas/**`, `porto_data/providers.json`, `porto_data/mappings.json`, `scripts/**`, or `cli/**` and has **no** changes under `tests/**`:

- **Title:** `Core data or validation logic changed without tests`
- **Body:** `Add or update focused tests in tests/ for the new or changed behavior.`
- **Labels:** `quality`, `tests`

### 2) Do not hand-edit metadata (blocking)

If a PR edits `porto_data/metadata.json` without related changes to data, schemas, mappings, or metadata generation (`scripts/generate_metadata.py`, `cli/commands/metadata.py`):

- **Title:** `metadata.json appears manually edited`
- **Body:** `Regenerate with make metadata (or porto metadata); do not edit checksums by hand.`
- **Labels:** `reliability`, `release`

### 3) Data / schema / mappings changes need refreshed metadata (blocking)

If a PR changes `porto_data/policy/**`, `porto_data/formats/**`, `porto_data/providers/**`, `porto_data/schemas/**`, or `porto_data/mappings.json` but **not** `porto_data/metadata.json`:

- **Title:** `Data or schema changed without metadata refresh`
- **Body:** `Run make metadata and commit porto_data/metadata.json in the same PR.`
- **Labels:** `quality`, `release`

### 4) New `subprocess.run` must not ignore failure (blocking)

In `scripts/**/*.py` or `cli/**/*.py`, new calls need `check=True` or explicit non-zero `returncode` handling.

Otherwise:

- **Title:** `subprocess.run without clear error handling`
- **Body:** `Use check=True or handle returncode explicitly.`
- **Labels:** `reliability`, `python`

### 5) No `sys.path` hacks (blocking)

If a PR adds `sys.path` mutation under `scripts/**` or `cli/**`:

- **Title:** `sys.path import hack introduced`
- **Body:** `Use package imports (from scripts... / from cli...) per project layout.`
- **Labels:** `python`, `maintainability`

### 6) JSON formatting drift (non-blocking)

If changed JSON under `porto_data/**` is minified, not 2-space indented, or keys reshuffled without need:

- **Title:** `JSON formatting or key-order drift`
- **Body:** `Keep 2 spaces, preserve key order, format with project tooling.`
- **Labels:** `maintainability`

### 7) User-visible contract changes → changelog (non-blocking)

If a PR changes published JSON contracts under `porto_data/policy/**`, `porto_data/formats/**`, `porto_data/providers/**`, `porto_data/schemas/**`, or `mappings.json` without `CHANGELOG.md`:

- **Title:** `User-visible data change without changelog update`
- **Body:** `Document notable consumer-facing changes in CHANGELOG.md.`
- **Labels:** `release-notes`

### 8) TODO/FIXME needs a tracker (non-blocking)

If new/changed code adds `TODO` or `FIXME` without an issue reference (`#123`, `ABC-123`):

- **Title:** `Untracked TODO/FIXME comment`
- **Body:** `Link to an issue or remove.`
- **Labels:** `maintainability`

---

## Data consistency and resolution

These rules align reviews with how **`GraphValidator`** (`scripts/validators/graph.py`) and **`validate_mappings_layout`** (`scripts/validators/mappings_layout.py`) protect the bundle. When in doubt, **`make validate`** (or `porto validate`) must pass for all providers.

### 9) Graph uses `edges`, not legacy `links` (blocking)

If a diff adds or keeps a **top-level** `"links"` key in any `porto_data/providers/**/graph.json`:

- **Title:** `graph.json must use top-level edges, not links`
- **Body:** `Resolution graphs use edges (product → zones + weight_tiers). Remove links or rename to edges per graph.schema.json.`
- **Labels:** `data`, `resolution`

### 10) Provider registry and mappings stay in lockstep (blocking)

If a PR changes the set of provider ids in **`porto_data/providers.json`** (`providers` object keys) or the keys under **`porto_data/mappings.json`** → **`mappings.providers`**, but **not** the other file in the same PR:

- **Title:** `Provider registry and mappings.json out of sync`
- **Body:** `Registry ids and mappings.providers keys must match; each registry id needs a provider folder and mappings entry.`
- **Labels:** `data`, `consistency`

### 11) New provider JSON must declare `provider` (blocking)

If a PR adds a new `*.json` under `porto_data/providers/<id>/` and the file is a mapped data document (not a stray file), and top-level **`provider`** is missing or not equal to **`<id>`**:

- **Title:** `Provider field must match folder id`
- **Body:** `Mapped provider JSON must include "provider": "<id>" matching the directory name (mappings validation).`
- **Labels:** `data`, `consistency`

### 12) Resolution graph edits need full validation (non-blocking)

If a PR changes any of **`graph.json`** (`edges`, `services`, `dependencies`), **`products.json`**, **`prices/products.json`**, **`prices/services.json`**, **`zones.json`**, or **`weights.json`** for a provider:

- **Title:** `Verify graph resolution and cross-file consistency`
- **Body:** `Run porto validate --type graph (or make validate) for that provider. Confirm edges reference existing product_ids; zones and weight_tiers match products and price rows; dependencies price paths are correct; services and price service_ids use native ids from services.json.`
- **Labels:** `resolution`, `consistency`

### 13) Validator changes must keep graph/mappings guarantees (blocking)

If a PR edits **`scripts/validators/graph.py`** or **`scripts/validators/mappings_layout.py`** without updates to **`tests/`** (or without clear refactor-only rationale in the description):

- **Title:** `Validator change without tests`
- **Body:** `Graph and layout validators enforce resolution and consistency; extend or adjust tests when behavior changes.`
- **Labels:** `quality`, `tests`

### 14) Schema changes for graph or catalogs need data alignment (non-blocking)

If a PR changes **`porto_data/schemas/graph.schema.json`** or schemas for **`products`**, **`prices`**, **`services`**, **`zones`**, or **`weights`**:

- **Title:** `Schema change — confirm all providers still validate`
- **Body:** `Run porto validate --type schema and full porto validate; update every provider’s JSON that must satisfy the new contract.`
- **Labels:** `data`, `consistency`
