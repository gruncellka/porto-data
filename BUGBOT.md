# Porto Data Bugbot Rules

## Scope

- Review rules for Bugbot in this `porto-data` tree only: data integrity, validation correctness, release safety.
- **Consistency** means cross-file agreement: registry ↔ mappings ↔ disk, **`policy/markets.json`** ↔ provider countries, catalog JSON ↔ **`graph.json`**, units, services ↔ prices ↔ graph, **`porto_id`** ↔ native ids.
- **Resolution** (for SDKs/loaders) is anchored in each provider’s **`graph.json`**: **`dependencies`**, **`edges`** (product × zones × weight tiers), top-level **`services`**, plus **`porto_data/schemas/graph.schema.json`**. Price lookup uses **`dependencies`** paths and price schemas join keys (`product_id`, `zone`, `weight_tier` / `service_id`). Loaders must not assume removed layouts (`porto_data/data/`, `data_links.json`, top-level **`links`**, **`lookup_rules`**, **`global_settings`**, **`price_lookup`**, or graph key **`available_services`** — use **`services`**).
- **Provider order** in docs and prose: **`deutschepost` → `ukrposhta` → `laposte` → `swisspost`**.
- **`limits.json`** with empty **`limits[]`** is **valid** — global restrictions live in **`policy/restrictions.json`**; overlays are optional.
- **JSON naming:** Porto-owned schema keys use full words (`international_currency`, `vat.domestic` / `vat.international`); see `.cursorrules` § JSON naming doctrine.
- Align with `.cursorrules`, **`.cursor/rules/catalog-layering-doctrine.mdc`**, and `CONTRIBUTING.md`.
- Do not flag files, workflows, or policies outside this repository.

## Catalog layering philosophy

porto-data ships **catalog facts** and **contracts** — not product workflow, compose layout, or SDK resolution logic. Reviewers and Bugbot should enforce **layer separation**, not only individual field names.

### Principles (apply to any PR touching catalog JSON or schemas)

1. **One identifier, one layer.** Native `id` wires graph/prices/rules. `porto_id` is SDK input only. `mark_profile` is layout output. `native_id` is adapter/API. Do not use the same token in two layers unless `docs/identity-map.md` documents the trap.

2. **Facts vs normalization vs workflow.** Tariff rows, mm geometry, and operator SKUs are facts. `porto_id` enums normalize cross-operator input. User choices (R1/R2, A-Post vs B-Post, sender placement) are resolved in SDK/app — **do not** encode them as new catalog fields when an existing layer already owns the fact.

3. **Disjoint vocabularies beat clever reuse.** If an enum value could mean two entity types (product size vs registered add-on), **split layers** — do not share the token. Product/service/feature `porto_id` disjointness is the reference pattern; apply the same instinct to geometry and marks.

4. **Validators > prose.** Invariants that matter for merge should fail in `scripts/validators/` + `tests/`. Flag PRs that document a rule only in markdown without CI enforcement.

5. **Generated docs must not hide drift.** Tools that rewrite docs (`docs/porto_id.md`, `metadata.json`) must fail when output differs from git — local “green” validate must not leave silent uncommitted contract drift.

### Canonical anti-patterns (already shipped fixes — do not reintroduce)

| Anti-pattern | Why wrong | Correct layer |
|--------------|-----------|---------------|
| `registered` on `products.porto_id` | Service semantics on size bucket | `small` + native id, or `services.porto_id` |
| `address_area` / `print_area` in layouts | Compose/workflow in catalog | `window` + `post_mark` only; compose in app |
| `porto_id` in `graph.json` / `prices/*` keys | SDK token in wiring | Native `product_id` / `service_id` |
| `mark_profile` id treated as `porto_id` | Layout vs input collapse | Resolve via `graph.edges.marks` |

See `docs/identity-map.md`, `docs/id.md`, `docs/formats.md`.

## Severity

- **Blocking:** correctness, safety, or release risk.
- **Non-blocking:** maintainability, coordination, or “verify before merge” resolution risk.

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

These rules align reviews with validators under `scripts/validators/` and **`make validate`** (same order as **`porto validate`**: schema → mappings → markets → limits → porto_ids → products_delivery → graph). Graph logic lives in package **`scripts/validators/graph/`** (not a single `graph.py` file).

### 9) Graph uses `edges` and `services`, not legacy keys (blocking)

If a diff adds or keeps a **top-level** `"links"` or `"available_services"` key in any `porto_data/providers/**/graph.json`:

- **Title:** `graph.json uses removed top-level keys`
- **Body:** `Use edges (product → zones + weight_tiers) and top-level services (native service ids). Remove links, available_services, lookup_rules, global_settings, price_lookup per graph.schema.json.`
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
- **Body:** `Run porto validate --type graph (or make validate) for that provider. Confirm edges reference existing product_ids; zones and weight_tiers match products and price rows; dependencies price paths are correct; graph services and price service_ids use native ids from services.json.`
- **Labels:** `resolution`, `consistency`

### 13) Validator changes must keep tests and coverage (blocking)

If a PR edits **`scripts/validators/**`** or **`cli/**`** without updates to **`tests/`** (or without clear refactor-only rationale in the description):

- **Title:** `Validator or CLI change without tests`
- **Body:** `Validators enforce resolution and consistency; extend or adjust tests when behavior changes. make test-cov requires 100% on scripts/ + cli/.`
- **Labels:** `quality`, `tests`

### 14) Schema changes for graph or catalogs need data alignment (non-blocking)

If a PR changes **`porto_data/schemas/graph.schema.json`**, **`markets.schema.json`**, **`porto_ids.schema.json`**, or schemas for **`products`**, **`prices`**, **`services`**, **`zones`**, or **`weights`**:

- **Title:** `Schema change — confirm all providers still validate`
- **Body:** `Run porto validate (or make validate) for all providers; update every JSON file that must satisfy the new contract.`
- **Labels:** `data`, `consistency`

### 15) Markets must be validated in CI (blocking)

If a PR changes validation tooling or **`.github/workflows/validation.yml`** and the workflow runs mappings / limits / porto_ids / graph but **not** `porto validate --type markets` (or equivalent **`validate-markets`** job):

- **Title:** `CI skips markets validation`
- **Body:** `make validate and pre-commit include markets between mappings and limits. Add a validate-markets job so policy/markets.json and provider country coverage cannot drift silently.`
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
- **Body:** `Use international in ids we assign (e.g. recommended_international). Preserve carrier-mirrored ids (lettre_recommandee_inter_r_un, international_standardbrief). Enforced in scripts/validators/porto_ids.py.`
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

### 23) Product `porto_id` is size-only — never service semantics (blocking)

If a PR adds or changes **`products.json`** so any product row’s **`porto_id`** is **not** one of the current **`product_porto_id`** enum values in **`porto_ids.schema.json`**, or uses tokens that belong on services/features — including but not limited to **`registered`**, **`registered_letter`**, **`registered_return_receipt`**, **`tracking`**, **`insurance`**, **`return_receipt`**, **`proof_of_mailing`**, **`proof_of_delivery`**, **`thickness`**, **`tracking_number`**, **`thickness_surcharge`**:

- **Title:** `Product row uses service/feature porto_id (or invented product token)`
- **Body:** `products.porto_id is a letter SIZE bucket only (small, medium, large, extra_large, postcard). Registered / recommandée / Einschreiben / tracking semantics belong on services.json or features.json, or are implied by native product id (e.g. La Poste lettre_recommandee_* → porto_id: small). Never put registered on a product row to mean “registered mail”. See docs/id.md and docs/resolution.md.`
- **Labels:** `data`, `consistency`, `resolution`

### 24) `product_porto_id` enum must stay disjoint from service/feature (blocking)

If a PR edits **`porto_ids.schema.json`** and **`product_porto_id`** shares any enum value with **`service_porto_id`** or **`feature_porto_id`**, or reintroduces **`registered`** (or any service/feature token) into the product enum:

- **Title:** `porto_id enum overlap — product vs service/feature`
- **Body:** `product_porto_id must not overlap service_porto_id or feature_porto_id. Service/feature may share tokens with each other where capability and priced add-on align (id.md). CI enforces via scripts/validators/porto_ids.py (_enum_overlap_errors) and test_live_schema_porto_id_enums_disjoint.`
- **Labels:** `data`, `consistency`

### 25) `porto_id` catalog changes need validator + mapping doc (blocking)

If a PR changes **`porto_ids.schema.json`**, any **`products.json`** / **`services.json`** / **`features.json`** `porto_id` field, or **`scripts/validators/porto_ids.py`**, but does **not** run **`porto validate --type porto_ids`** (or full **`make validate`**) so **`docs/porto_id.md`** and tests stay current:

- **Title:** `porto_id change without validation / mapping doc refresh`
- **Body:** `Run porto validate --type porto_ids (or make validate). Commit regenerated docs/porto_id.md when drift is detected. Extend tests/test_porto_ids.py when validator behavior changes.`
- **Labels:** `quality`, `consistency`

### 26) Catalog must not encode compose / workflow semantics (blocking)

If a PR adds or restores layout or format fields that describe **addressing workflow**, **sender/recipient placement**, **printable regions**, or other **app compose** concerns — e.g. **`address_area`**, **`print_area`**, `margins_mm` derived from invented print zones, or product fields that duplicate UI resolution:

- **Title:** `Workflow semantics leaked into catalog JSON`
- **Body:** `porto-data owns factual geometry (layouts: window, post_mark, standard) and tariff facts. Compose and addressing belong in SDK/app. Do not reintroduce removed layout zones or invent catalog fields to shortcut resolution.`
- **Labels:** `data`, `architecture`, `consistency`

### 27) Cross-layer identifier misuse (blocking)

If a PR uses **`porto_id`** (or other SDK-normalization tokens) in **`graph.json`**, **`prices/*.json`**, or **`rules.json`** keys/refs where **native `id`** is required — or conflates **`mark_profile`** ids / **zone** ids with **`porto_id`** without updating `docs/identity-map.md`:

- **Title:** `Wrong identifier layer in catalog wiring`
- **Body:** `graph, prices, rules: native product_id / service_id only. porto_id is SDK input. mark_profile and zone are separate namespaces. See docs/identity-map.md.`
- **Labels:** `data`, `resolution`, `consistency`

### 28) New schema field without clear owning layer (non-blocking)

If a PR adds properties to **`porto_data/schemas/**`** or new top-level keys in provider/catalog JSON without stating (in PR description or adjacent docs) **which layer** owns the fact (fact vs normalization vs layout output vs runtime):

- **Title:** `New catalog field — confirm owning layer`
- **Body:** `Apply catalog layering philosophy (BUGBOT.md § Catalog layering philosophy). Ask: is this a carrier fact, SDK porto_id, compose concern, or runtime-only? Prefer validators over prose-only rules.`
- **Labels:** `architecture`, `maintainability`

### 29) Invariant documented but not enforced in validators (non-blocking)

If a PR adds normative rules only to **`docs/*.md`** or **`.cursorrules`** for catalog behavior that **`make validate` does not check**, and the invariant is machine-checkable:

- **Title:** `Catalog rule lacks validator coverage`
- **Body:** `Encode checkable invariants in scripts/validators/ + tests/ (make test-cov). Examples: porto_id enum disjointness, layout window-only geometry, native-id refs in prices/graph.`
- **Labels:** `quality`, `tests`

### 30) Product delivery must cover every zone (blocking)

If a PR adds or changes **`products.json`** and any product’s **`delivery[]`** zones do not **exactly partition** **`product.zones`** (missing zone, extra zone, or duplicate zone across entries):

- **Title:** `Product delivery zone coverage mismatch`
- **Body:** `Each product.delivery[] entry lists zone ids; union must equal product.zones exactly once each. CI: porto validate --type products_delivery. See docs/resolution.md § Delivery hints.`
- **Labels:** `data`, `consistency`

### 31) No SDK speed-class `lane` on products (blocking)

If a PR adds **`lane`**, **`priority`**, **`economy`**, or similar interpreter enums on **`products.json`** or **`products.schema.json`** to mean carrier speed class:

- **Title:** `Speed class belongs in SDK, not catalog`
- **Body:** `Catalog stores operator time facts (delivery span + days per zone) and markets.working_days calendar. Disambiguation (A-Post vs B-Post) uses native product id or delivery hints — not a normalized lane enum.`
- **Labels:** `data`, `architecture`, `consistency`

### 32) Product indemnity and twin disambiguation (blocking)

If a PR adds or changes **`products.json`** and:

- any La Poste **`lettre_recommandee_*`** row lacks **`indemnity`**, or a non-recommandée La Poste row sets **`indemnity`**, or **`indemnity.tier`** does not match the product id (R1/R2/R3), or
- two products share the same **`(porto_id, zone, weight_tier)`** graph edge and identical resolution fingerprint (`delivery[]` sig, **`indemnity.tier`**, **`included_features`**, **`tracking_mode`**), or
- **`included_features[]`** references an id missing from provider **`features.json`**:

- **Title:** `Product resolution facts invalid or ambiguous twins`
- **Body:** `Recommandée must carry indemnity; twins must differ on delivery, indemnity.tier, included_features, or tracking_mode. CI: porto validate --type products_delivery. See docs/resolution.md § Candidate enrichment.`
- **Labels:** `data`, `consistency`, `resolution`
