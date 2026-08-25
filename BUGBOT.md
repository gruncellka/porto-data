# Porto Data Bugbot Rules

## Scope

- Review **this `porto-data` tree only**: integrity, validators, release safety.
- Layer philosophy: [`.cursor/rules/data.mdc`](.cursor/rules/data.mdc) · `docs/identity.md` — do not restate here.
- Consistency: registry ↔ mappings ↔ disk; markets ↔ providers; catalog ↔ `graph.json`; `kind` ↔ native ids.
- Resolution: `graph.json` (`dependencies`, `edges`, `edges.wire`, `services`) + optional `execution.json` (wire + billing/execution tokens only — not wire tables).
- Provider order in prose: `deutschepost` → `ukrposhta` → `laposte` → `swisspost`.
- Empty `limits.json` `limits[]` is valid (global restrictions in `policy/restrictions.json`).
- Align with `.cursorrules`, `data.mdc`, `CONTRIBUTING.md`.

## Anti-patterns (do not reintroduce)

| Anti-pattern | Correct layer |
|--------------|---------------|
| `registered` on `products.json` | native product id / `services.kind` |
| `kind` or `porto_id` on products | concrete `products.id` only |
| `address_area` / `print_area` in layouts | `window` + `post_mark`; compose in app |
| `kind` as graph/prices keys | native `product_id` / `service_id` |
| `productCode` in `execution.json` | `graph.edges.wire` |
| `native_id` on product/service rows | `edges.wire` |
| Compose blocks in `layouts.json` | `formats/addresses.json` |

## Severity

- **Blocking:** correctness, safety, or release risk.
- **Non-blocking:** maintainability or verify-before-merge.

## Rules

### 1) Data or schema changes need test updates (blocking)

If a PR changes `porto_data/policy/**`, `porto_data/formats/**`, `porto_data/providers/**`, `porto_data/schemas/**`, `porto_data/providers.json`, `porto_data/mappings.json`, `scripts/**`, or `cli/**` and has **no** changes under `tests/**`:

- **Title:** `Core data or validation logic changed without tests`
- **Body:** `Add or update focused tests in tests/ for the new or changed behavior. Target 100% coverage on scripts/ + cli/ (make test-cov).`
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
- **Body:** `Keep 2 spaces, preserve key order, format with make format-json or scripts/format_json_file.py.`
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

These rules align reviews with validators under `scripts/validators/` and **`make validate`** (same order as **`porto validate`**: schema → mappings → markets → addresses → limits → kinds → delivery → graph). Graph logic lives in package **`scripts/validators/graph/`** (not a single `graph.py` file).

### 9) Graph uses `edges` and `services`, not legacy keys (blocking)

If a PR adds or keeps a **top-level** `"links"` or `"available_services"` key in any `porto_data/providers/**/graph.json`, or reintroduces **`services.integrations`**:

- **Title:** `graph.json uses removed top-level keys`
- **Body:** `Use edges (product → zones + weight_tiers; wire under edges.wire) and top-level services (native service ids). Remove links, available_services, services.integrations, lookup_rules, global_settings, price_lookup per graph.schema.json. Execution manifest: execution.json.`
- **Labels:** `data`, `resolution`

### 10) Provider registry and mappings stay in lockstep (blocking)

If a PR changes the set of provider ids in **`porto_data/providers.json`** (`providers` object keys) or the keys under **`porto_data/mappings.json`** → **`mappings.providers`**, but **not** the other file in the same PR:

- **Title:** `Provider registry and mappings.json out of sync`
- **Body:** `Registry ids and mappings.providers keys must match; each registry id needs a provider folder and mappings entry.`
- **Labels:** `data`, `consistency`

### 11) New provider JSON must declare `provider` (blocking)

If a PR adds a new `*.json` under `porto_data/providers/<id>/` and the file is a mapped data document (not a stray file), and top-level **`provider`** is present on a path-scoped file:

- **Title:** `Do not repeat provider on path-scoped JSON`
- **Body:** `Provider id is implied by directory path providers/<id>/ — mapped files must not include a redundant top-level "provider" field (mappings_layout validation errors if present).`
- **Labels:** `data`, `consistency`

### 12) Resolution graph edits need full validation (non-blocking)

If a PR changes any of **`graph.json`** (`edges`, `services`, `dependencies`), **`products.json`**, **`prices/products.json`**, **`prices/services.json`**, **`zones.json`**, or **`weights.json`** for a provider:

- **Title:** `Verify graph resolution and cross-file consistency`
- **Body:** `Run porto validate --type graph (or make validate) for that provider. Confirm edges reference existing product_ids; zones and weight_tiers match products and price rows; dependencies price paths are correct; graph services and price service_ids use native ids from services.json.`
- **Labels:** `resolution`, `consistency`

### 13) Validator changes must keep tests and coverage (blocking)

If a PR edits **`scripts/validators/**`** or **`cli/**`** without updates to **`tests/`** (or without clear refactor-only rationale in the description):

- **Title:** `Validator or CLI change without tests`
- **Body:** `Validators enforce resolution and consistency; extend or adjust tests when behavior changes. make test-cov requires 100% on scripts/ + cli/.`
- **Labels:** `quality`, `tests`

### 14) Schema changes for graph or catalogs need data alignment (non-blocking)

If a PR changes **`porto_data/schemas/graph.schema.json`**, **`markets.schema.json`**, **`kinds.schema.json`**, **`addresses.schema.json`**, or schemas for **`products`**, **`prices`**, **`services`**, **`zones`**, or **`weights`**:

- **Title:** `Schema change — confirm all providers still validate`
- **Body:** `Run porto validate (or make validate) for all providers; update every JSON file that must satisfy the new contract.`
- **Labels:** `data`, `consistency`

### 15) Markets must be validated in CI (blocking)

If a PR changes validation tooling or **`.github/workflows/validation.yml`** and the workflow runs mappings / limits / kinds / graph but **not** `porto validate --type markets` (or equivalent **`validate-markets`** job) or **not** `porto validate --type addresses` (or equivalent **`validate-addresses`** job):

- **Title:** `CI skips markets or addresses validation`
- **Body:** `make validate and pre-commit include markets then addresses between mappings and limits. Add validate-markets and validate-addresses jobs so policy/markets.json and formats/addresses.json cannot drift silently.`
- **Labels:** `ci`, `consistency`

### 16) Markets validator must cover all registry providers (blocking)

If **`scripts/validators/markets.py`** (or equivalent) iterates only a fixed provider tuple (e.g. **`PROVIDER_IDS_ORDER`**) and skips other ids present in **`providers.json`**:

- **Title:** `Markets check ignores extra registry providers`
- **Body:** `Every providers.json entry with a country must have a matching markets[CC] row; walk the full registry, not a hard-coded subset.`
- **Labels:** `data`, `consistency`

### 17) Do not require rows in empty limits.json (non-blocking)

If a review comment treats **`limits[]`: []** or **`frameworks`: {}** in **`providers/*/limits.json`** as incomplete or missing compliance data:

- **Title:** `Empty limits.json is intentional`
- **Body:** `Sanctions and destination regimes belong in policy/restrictions.json. limits.json is an optional provider overlay slot; empty is the expected steady state until a citable operator letter rule is modeled.`
- **Labels:** `docs`, `consistency`

### 18) VAT and currency belong in markets, not providers.json (blocking)

If a PR adds **`vat`** or per-provider default currency fields to **`providers.json`** instead of **`policy/markets.json`**:

- **Title:** `Fiscal defaults must use policy/markets.json`
- **Body:** `providers.json carries identity and country; markets[country].currency / vat / international_currency hold fiscal defaults.`
- **Labels:** `data`, `consistency`

### 19) Deprecated international/currency abbreviations in markets (blocking)

If a PR adds or keeps **`intl_ccy`**, **`intl_excl`**, top-level **`vat.inclusive`** (without `vat.domestic` / `vat.international`), or other `intl`/`ccy` abbreviations in **`policy/markets.json`** or **`markets.schema.json`**:

- **Title:** `Use full international/currency key names in markets`
- **Body:** `Porto keys: international_currency (not intl_ccy); vat.domestic.inclusive and vat.international.inclusive (not intl_excl or flat vat.inclusive). See JSON naming doctrine in .cursorrules.`
- **Labels:** `data`, `consistency`

### 20) Porto-assigned native ids must not use _intl suffix (blocking)

If a PR adds a **new** native product or service `id` ending in **`_intl`** (Porto-assigned naming; carrier tokens like `inter_r` are OK):

- **Title:** `Native id uses deprecated _intl suffix`
- **Body:** `Native ids must be local-language slugs of the operator display name (see docs/provider-template.md). Avoid English semantic ids and abbreviated locale tokens. _intl suffix is deprecated for new ids. Enforced in scripts/validators/kinds.py.`
- **Labels:** `data`, `consistency`

### 21) Market row key order (non-blocking)

If `markets[CC]` uses deprecated keys or puts `vat` before `currency`:

- **Title:** `Market row key order / naming drift`
- **Body:** `Order: currency → international_currency → vat → settlement. No intl_ccy.`
- **Labels:** `maintainability`, `consistency`

### 22) Provider order in registry, mappings, metadata, and docs (non-blocking)

If a PR lists operators out of bundle order **`deutschepost` → `ukrposhta` → `laposte` → `swisspost`** (README carrier table, doc link rows, `providers.json` / `mappings.json` / `metadata.json` key order):

- **Title:** `Provider order drift`
- **Body:** `Use canonical order deutschepost → ukrposhta → laposte → swisspost in prose, tables, and JSON object keys. Enforced in mappings validation for registry/mappings/metadata.`
- **Labels:** `maintainability`, `consistency`

### 23) Products must not have `kind` or `porto_id` (blocking)

If a PR adds or changes **`products.json`** so any product row includes **`kind`**, **`porto_id`**, or other cross-provider taxonomy fields:

- **Title:** `Product row uses kind or porto_id (removed)`
- **Body:** `Products have concrete id only. Registered / recommandée / Einschreiben semantics belong on services.json (kind) or are implied by native product id (e.g. La Poste lettre_recommandee_*). Never put kind or porto_id on a product row. See docs/id.md and docs/resolution.md.`
- **Labels:** `data`, `consistency`, `resolution`

### 24) Service/feature `kind` must match `kinds.schema.json` (blocking)

If a PR edits **`kinds.schema.json`** or any **`services.json`** / **`features.json`** `kind` field with values outside the canonical enums, or reintroduces **`porto_id`** on service/feature rows:

- **Title:** `Invalid or legacy kind on catalog row`
- **Body:** `Services and features use kind (not porto_id). Enum source: kinds.schema.json. Service/feature may share tokens where capability and priced add-on align (id.md). CI enforces via scripts/validators/kinds.py and tests/test_kinds.py.`
- **Labels:** `data`, `consistency`

### 25) `kind` catalog changes need validator + mapping doc (blocking)

If a PR changes **`kinds.schema.json`**, any **`services.json`** / **`features.json`** `kind` field, or **`scripts/validators/kinds.py`**, but does **not** run **`porto validate --type kinds`** (or full **`make validate`**) so **`docs/kinds.md`** and tests stay current:

- **Title:** `kind change without validation / mapping doc refresh`
- **Body:** `Run porto validate --type kinds (or make validate). Commit regenerated docs/kinds.md when drift is detected. Extend tests/test_kinds.py when validator behavior changes.`
- **Labels:** `quality`, `consistency`

### 26) Catalog must not encode compose / workflow semantics (blocking)

If a PR adds or restores layout or format fields that describe **addressing workflow**, **sender/recipient placement**, **printable regions**, or other **app compose** concerns — e.g. **`address_area`**, **`print_area`**, `margins_mm` derived from invented print zones, or product fields that duplicate UI resolution:

- **Title:** `Workflow semantics leaked into catalog JSON`
- **Body:** `porto-data owns factual geometry (layouts: window, post_mark, standard) and tariff facts. Compose and addressing belong in SDK/app. Do not reintroduce removed layout zones or invent catalog fields to shortcut resolution.`
- **Labels:** `data`, `architecture`, `consistency`

### 27) Cross-layer identifier misuse (blocking)

If a PR uses **`kind`** (or other cross-provider tokens) in **`graph.json`**, **`prices/*.json`**, or **`rules.json`** keys/refs where **native `id`** is required — or conflates **`mark_profile`** ids / **zone** ids with **`kind`** without updating `docs/identity.md`:

- **Title:** `Wrong identifier layer in catalog wiring`
- **Body:** `graph, prices, rules: native product_id / service_id only. kind is consumer intent on services/features. mark_profile and zone are separate namespaces. See docs/identity.md.`
- **Labels:** `data`, `resolution`, `consistency`

### 28) New schema field without clear owning layer (non-blocking)

If a PR adds properties to **`porto_data/schemas/**`** or new top-level keys in provider/catalog JSON without stating (in PR description or adjacent docs) **which layer** owns the fact (fact vs normalization vs layout output vs runtime):

- **Title:** `New catalog field — confirm owning layer`
- **Body:** `Apply catalog layering philosophy (BUGBOT.md § Catalog layering philosophy). Ask: is this a carrier fact, cross-provider kind, compose concern, or runtime-only? Prefer validators over prose-only rules.`
- **Labels:** `architecture`, `maintainability`

### 29) Invariant documented but not enforced in validators (non-blocking)

If a PR adds normative rules only to **`docs/*.md`** or **`.cursorrules`** for catalog behavior that **`make validate` does not check**, and the invariant is machine-checkable:

- **Title:** `Catalog rule lacks validator coverage`
- **Body:** `Encode checkable invariants in scripts/validators/ + tests/ (make test-cov). Examples: kind enum validation, layout window-only geometry, native-id refs in prices/graph.`
- **Labels:** `quality`, `tests`

### 30) Product delivery must cover every zone (blocking)

If a PR adds or changes **`products.json`** and any product’s **`delivery[]`** zones do not **exactly partition** **`product.zones`** (missing zone, extra zone, or duplicate zone across entries):

- **Title:** `Product delivery zone coverage mismatch`
- **Body:** `Each product.delivery[] entry lists zone ids; union must equal product.zones exactly once each. CI: porto validate --type delivery. See docs/resolution.md § Delivery hints.`
- **Labels:** `data`, `consistency`

### 31) No SDK speed-class `lane` on products (blocking)

If a PR adds **`lane`**, **`priority`**, **`economy`**, or similar interpreter enums on **`products.json`** or **`products.schema.json`** to mean carrier speed class:

- **Title:** `Speed class belongs in SDK, not catalog`
- **Body:** `Catalog stores operator time facts (delivery span + days per zone) and markets.working_days calendar. Disambiguation (A-Post vs B-Post) uses native product id or delivery hints — not a normalized lane enum.`
- **Labels:** `data`, `architecture`, `consistency`

### 32) Product indemnity and twin disambiguation (blocking)

If a PR adds or changes **`products.json`** and:

- any La Poste **`lettre_recommandee_*`** row lacks **`indemnity`**, or a non-recommandée La Poste row sets **`indemnity`**, or **`indemnity.tier`** does not match the product id (R1/R2/R3), or
- two products share the same **`(zone, weight_tier)`** graph edge and identical resolution fingerprint (`delivery[]` sig, **`indemnity.tier`**, **`included_features`**, **`tracking`**), or
- **`included_features[]`** references an id missing from provider **`features.json`**:

- **Title:** `Product resolution facts invalid or ambiguous twins`
- **Body:** `Recommandée must carry indemnity; twins must differ on delivery, indemnity.tier, included_features, or tracking. CI: porto validate --type delivery. See docs/resolution.md § Candidate enrichment.`
- **Labels:** `data`, `consistency`, `resolution`

### 33) Execution manifest vs wire tables (blocking)

If a PR adds or changes **`execution.json`** and:

- puts **`productCode`**, zone wire rows, or other checkout catalog keys in the manifest instead of **`graph.edges.wire`**, or
- sets **`wire`** to a value that does not match an **`edges.wire`** key, or
- duplicates manifest data under **`graph.dependencies.execution`** (beyond the file pointer), or
- reintroduces **`services.integrations`** on **`graph.json`**:

- **Title:** `Execution manifest conflated with wire tables`
- **Body:** `execution.json owns wire + billing[]/execution[] only. Wire productCode tables live in graph.edges.wire[wire]. dependencies.execution is a bundle index pointer. CI: scripts/validators/graph/execution_manifest.py. See docs/identity.md.`
- **Labels:** `data`, `architecture`, `consistency`

### 34) Wire codes must not live on catalog entity rows (blocking)

If a PR adds **`native_id`**, **`productCode`**, or adapter checkout keys on **`products.json`** / **`services.json`** rows (or in schemas as required catalog fields) instead of **`graph.edges.wire`**:

- **Title:** `Adapter wire code on catalog entity row`
- **Body:** `Checkout catalog keys are per wire in graph.edges.wire (product × zone [× service composite]). products/services keep operator native id; services/features may carry kind. CI: wire_edges entity guard.`
- **Labels:** `data`, `resolution`, `consistency`

### 35) Mark calibrations must align with wire ids (blocking)

If a PR adds or changes **`marks.json`** **`calibrations[]`** and:

- **`wire`** does not match a key under **`graph.edges.wire`**, or
- **`calibrations[].mark_profile`** is missing, or **`by_mark_profile`** keys are unknown to **`marks.profiles`**, or
- measured checkout sizes are documented only in **`docs/marks.md`** instead of **`docs/providers/<id>.md`** for operator-specific tables:

- **Title:** `Mark calibrations invalid or misplaced`
- **Body:** `calibrations[].wire must match edges.wire. calibrations[].mark_profile is the wire checkout layout token (not voucher_layout). FRANKING_ZONE uses by_mark_profile keyed by Porto profile id; ADDRESS_ZONE uses shared label_canvas. Operator tables belong in docs/providers/<id>.md. CI: scripts/validators/graph/marks_profiles.py.`
- **Labels:** `data`, `consistency`

### 36) Execution schema / mappings must stay in lockstep (blocking)

If a PR adds **`execution.json`** for a provider but omits **`execution.schema.json`**, **`mappings.json`** entry, **`graph.dependencies.execution`**, or **`make validate`** / tests for **`execution_manifest`**:

- **Title:** `execution.json added without schema, index, or validator`
- **Body:** `Register execution manifest in mappings; point from graph.dependencies.execution; validate wire vs edges.wire keys. Add tests in tests/test_graph_execution_manifest.py. Run make validate and commit metadata.json when data changes.`
- **Labels:** `quality`, `data`, `consistency`

### 37) Address forms stay in addresses.json (blocking)

If a PR adds or changes **`formats/addresses.json`** / **`formats/layouts.json`** and:

- puts sender/recipient or compose zones on **`layouts.json`**, or
- treats **`addresses.json`** as a world directory (rows without cited postal facts), or
- adds **`addresses.json`** without **`addresses.schema.json`**, mappings/formats index, **`scripts/validators/addresses.py`**, or tests, or
- lets **`standard`** disagree with **`layouts.json`** for a jurisdiction that has layouts:

- **Title:** `Address forms misplaced or unvalidated`
- **Body:** `Forms (street/post_box, postcode pattern) live in formats/addresses.json. Layouts keep window/post_mark/standard only. Sparse jurisdictions; layout standard match when layouts[CC] exists. CI: porto validate --type addresses. See docs/formats.md and docs/identity.md.`
- **Labels:** `data`, `architecture`, `consistency`
