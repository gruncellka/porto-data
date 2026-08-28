# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [0.7.0] - 2026-08-28

### Added

- **`jurisdictions[].country_code_3`:** ISO 3166-1 alpha-3 on every per-country row (companion to the alpha-2 map key); required in `jurisdictions.schema.json`. Blocs `EU` / `UN` stay members + timezone only.
- **`service_prices[].zone`:** optional zone id so add-on amounts can vary by zone (same join as `product_prices`). Deutsche Post `einschreiben`: 265 domestic, 370 on `zone_1_eu` / `zone_2_europe` / `world`. Omit `zone` when one amount covers every `supported_zones` entry.
- **`marks.placement.envelopes`:** per-envelope franking rectangle (mm, origin top-left). Deutsche Post Internetmarke **74×40** from top-right (Frankiervermerk-Merkblatt / IM FAQ). La Poste MTEL **74×40** from top-right (Guide pratique courrier — La Poste original, not copied from DE). Swiss Post WebStamp **74×38** from top-right (post.ch couvert templates); size⊆placement is skipped for Swiss while catalog stamp **40×40** is nominal. Ukrposhta eCom **omits** placement (label, not an envelope-face stamp). Optional **`profiles[].clearance`** (mm around the graphic); omit unless the operator requires it for that graphic. No `tolerance`.
- **`layouts.UA`:** ДСТУ 3876-99 window facts (C6/DL/C5 **90×45** bottom-right; C4/B4 no window). Address `UA.standard` is **`DSTU3876`**.

### Changed

- **CI / Make / pre-commit naming:** validation workflow jobs, Make targets, and hook IDs use short concern names (`schema`, `format`, `lint`, `types`, `test`, `mappings`, …, `validate` aggregator). Independent leaves run in parallel; `validate` is the branch-protection check.
- **Catalog descriptions:** neutralize graph dependency blurbs and product/service/feature copy — factual operator wording only; drop implementor notes (wire/API, file paths, resolver hints).
- **Docs / rules:** address place field documented as **`locality`** (UPU); catalog key wording prefers **catalog `id`** over “native id” in contributor rules. Policy docs stay catalog-layer (no SDK result shape).

### Changed (breaking)

- **Restrictions legal `frameworks` → `jurisdictions`:** map keys are `jurisdictions.json` identifiers (`EU` \| `CH` \| `UA`) to instrument arrays (`reference`, `effective_from`, optional `effective_to`). Legal rows keep short neutral `reason` / `description` (not political labels). Routing keeps `authority` / `reference` / `reason` / `description` and must not have `jurisdictions`. `partial: true` unchanged (absent = full coverage of the represented region).
- **Restrictions:** collections are country-keyed maps (`legal`, `routing`), then region-keyed maps. No `operational` collection. No record `id`. No top-level `sources` array. Machine impact (`block` \| `warn`) is resolved by the SDK, not stored in the catalog. Load fails closed without required fields. Census: UA legal facts and Cyprus routing.
- **Drop `limits.json`:** no per-provider overlay file, schema, graph node, mapping, or `porto validate --type limits`.
- **Address form field `city` → `locality`:** UPU postal vocabulary (`locality` covers town/village/place; `city` is ambiguous). Enum in `addresses.schema.json` and all `forms[].required` entries.
- **Envelope face `standards[]`:** `envelopes.json` cites **ISO 269** and **DIN 678** together; drop singular `standard`. DL/C-series faces are worldwide formats, not DE-owned sizes copied globally.
- **Layouts drop `post_mark`.** `layouts.json` holds shared/jurisdiction-standard **window** facts only (DIN 680-style windows may match across DE/CH/FR because they share a window norm — that is not “DE copied”). Mark **placement** lives on provider `marks.json`.
- **Drop `porto_id`.** Catalog identity is concrete `id` only (`name` native, `label` English). Products have no size bucket / `kind`. Country + weight + zone are the core facts; optional envelope **filters** `envelope_ids[]` (does not select a product). Pin with `product_id` / `service_ids`; `services` is `kind` intent. Graph, prices, and `services[].features[]` stay on `id`.
- **Docs:** consumer input splits `kind` vs catalog `id` (no “kind or id” slot; catalog keys are not “native id”). Envelope is a fit filter; several remaining rows is selection or ambiguity.
- **`porto_ids.schema.json` → `kinds.schema.json`**; `porto validate --type kinds` regenerates `docs/kinds.md` (removed `docs/porto_id.md`). Kind renames: `proof_of_mailing` → `acceptance_proof`, `proof_of_delivery` → `delivery_proof`.
- Optional **`requires`** (`ADDRESS_SENDER` / `ADDRESS_RECIPIENT`) on product, service, feature, and mark profile (omit when unused; no empty arrays).
- Marks: `profiles[].type` replaces `profiles[].mark_type`; drop `presentations[]` (checkout layout is wire, not catalog).

## [0.6.0] - 2026-08-24

### Added

- **English `label` on products and zones:** Required `label` (English UI/tooling) alongside native `name` on all provider `products.json` and `zones.json` rows; schemas updated.
- **SDK catalog compat:** porto-data **package version is the schema version** (`metadata.project.version`). SDKs gate load on that semver (`PORTO_DATA_SCHEMA_UNSUPPORTED` / `PORTO_DATA_SCHEMA_TOO_NEW`). See Lab [versioning-architecture-review.md](../../docs/sdks/versioning-architecture-review.md).
- **Address forms (`formats/addresses.json`):** Sparse jurisdiction postal validity (DE/CH/FR/UA) with `forms[]` kinds `street` | `post_box`, `postal_code.pattern`, and FR `max_line_length` 38. Layout-aligned standards for DE/CH/FR; UA address-only `UKRPOSHTA` until `layouts.UA` exists. Schema + validator (layout match only when layout jurisdiction present).
- **Graph validator:** `execution_manifest` requires at least one billing or execution capability token when the manifest exists.

### Changed

- **Shared schema descriptions:** Neutralized vendor-specific wording in `marks`, `graph`, and `services` schema descriptions.
- **Jurisdiction blocs:** Uppercase bloc keys `jurisdictions.eu` / `jurisdictions.un` → `EU` / `UN` so they match restriction buckets `EU` / `UN` / `CH`. Schema excludes `EU`/`UN` from country timezone `patternProperties` (blocs keep `members` + `timezone`).
- **Ukrposhta feature native id:** Rename `recipient_signature` → `osobyste_vruchennia` (keep `porto_id: recipient_signature`); service feature refs updated.
- **Vocabulary:** Drop SDK type/method spine from porto-data docs (`identity.md`, BUGBOT, `.cursorrules`); keep catalog layer boundaries only. Graph validator helper `wire_integration_ids` → `wire_ids`. Identity cheat sheet `capability` → `billing[]` / `execution[]`. BUGBOT `edges.wire[wire]`. Validation chain includes **`addresses`** (Cursor rules, CONTRIBUTING, BUGBOT rule 37, pre-commit + CI job).
- **`execution.schema.json`:** Capability description no longer says “Postage execution…”.

### Changed (breaking)

- **Restrictions:** Drop `entity_type` (`country` | `territory` | `disputed`) from restriction items and schemas. Geography stays `destinations[].country_code` plus optional item `region_code` (ISO 3166-2) / `partial` — no political class. Same unused enum removed from `limits.schema.json`.
- **Product `porto_id`:** Drop unused `postcard` from `porto_ids.schema.json` and docs (`id.md`, `identity.md`, BUGBOT, `.cursorrules`). Size buckets are `small` … `extra_large` only.
- **Execution capability tokens:** `create_mark` → `mark`, `get_wallet_balance` → `wallet` in `execution.json` / `execution.schema.json`.
- **Feature `porto_id`:** `tracking_number` → `tracking`, `thickness_surcharge` → `thickness` (share the matching service tokens).
- **`products.tracking_mode` → `tracking`** (`none` \| `optional` \| `included`). Same English word as service/feature `porto_id` `tracking` — see `docs/identity.md`.
- **Dropped service fields:** `enables_tracking`, `online_supported`, `source_id`. Tracking on a service is derived: `features[]` resolves (native id or `porto_id`) to a feature whose `porto_id` is `tracking`. Online orderability is a wire fact.
- **Execution manifest:** Rename `integration.json` → `execution.json`, `integration.schema.json` → `execution.schema.json`, `file_type` `integration` → `execution`, manifest field `adapter` → `wire`, and `graph.dependencies.integration` → `graph.dependencies.execution`.
- **Provider-scoped JSON:** Drop redundant top-level `provider` on every file under `providers/<id>/` — folder path is SoT; keep `file_type` for schema routing.
- **Native catalog ids:** Normalize operator-assigned keys to local-language slugs (`maxibrief_ausland`, `option_suivi`, `zuschlag_dicke`, …) — no English semantic ids or abbreviated locale tokens (`inter`, `heavy`).
- **Ukrposhta registered intl service:** `Міжнародне зареєстроване` / `mizhnarodne_zareiestrovane` (was реєстрування / `mizhnarodne_reiestruvannia`).

### Fixed

- **Deutsche Post `zusatzversicherung`:** do not list feature `tracking` — Zusatzversicherung is priced insurance, not Sendungsnummer. `services[].features` may be empty.
- **Layout window geometry (DIN 680 Form B):** C5/C4 `window.area.y` for DE/CH/FR was incorrectly using the DL/C6 15 mm-from-bottom rule (`y` 102 / 159). Corrected to Form B: C5 `y: 57` (60 mm from bottom), C4 `y: 57` (57 mm from top).
- **`marks_profiles` calibrations:** Require ``calibrations[].mark_profile`` (wire checkout layout token), matching schema + Deutsche Post data — not legacy ``voucher_layout``.

## [0.5.1] - 2026-07-07

### Added

- **`integrations.schema.json`:** Per-operator execution adapter manifest (`adapter`, `capabilities[]`).
- **Deutsche Post `integrations.json`:** Internetmarke adapter with `mark_purchase_sync` and `wallet_balance_read`.
- **Deutsche Post `marks.json`:** `calibrations[]` for Internetmarke `FRANKING_ZONE` (per `mark_profile`) and `ADDRESS_ZONE` full label canvas (85×43 mm at checkout dpi 300).
- **`marks.schema.json`:** Optional `calibrations[]` (wire × mark_profile × checkout dpi × px/mm).
- **Graph validators:** `integrations_manifest` (adapter vs `edges.wire`); `marks_profiles` calibration cross-checks.

### Fixed

- **Deutsche Post `edges.wire.internetmarke` (domestic):** Restore correct Internetmarke `productCode` values for base products and Einschreiben composites (e.g. `standardbrief` domestic `1` / `1007`, not `10001` / `10007`).
- **`graph.dependencies.integrations`:** Clarified description — manifest holds adapter + capabilities; wire codes remain in `edges.wire`.

### Changed

- **Docs:** Renamed `identity-map.md` → [identity.md](docs/identity.md) and `mark-profiles.md` → [marks.md](docs/marks.md); Deutsche Post mark tables and Internetmarke calibrations live in [providers/deutschepost.md](docs/providers/deutschepost.md).
- **`marks.schema.json`:** Provider-neutral calibration field descriptions (no operator-specific examples in shared contract).
- **Governance:** Cursor rules and `BUGBOT.md` rules 33–36 for integrations vs wire layering and mark calibrations.

## [0.5.0] - 2026-07-06

### Changed (breaking)

- **`graph.json`:** Required **`strategy`** (`service` | `id` | `speed` | `min`); optional **`edges.wire`** for adapter catalog codes per integration.
- **Entity schemas:** Removed **`products.native_id`**, **`products.zone_native_ids`**, **`services.native_id`**, and **`services.product_native_ids`**. Wire codes are owned by **`graph.edges.wire`** only.
- **`services.integrations`:** Removed — redundant with **`online_supported`** and **`graph.edges.wire`** integration keys.
- **All four providers:** Migrated Internetmarke / MTEL / WebStamp / Ukrposhta eCom wire tables into graph; DE composite Einschreiben codes moved off `services.json`.
- **La Poste / Swiss Post wire:** `base` populated with stable catalog keys (`product.id`) pending live API SKU harvest.
- **`marks.schema.json`:** Removed `image/jpeg` from allowed profile MIME types (PNG/PDF only).

### Fixed

- **Deutsche Post `edges.wire.internetmarke` (domestic):** Restore full 5-digit `productCode` values (bases and Einschreiben composites); CSV import had truncated leading zeros.

### Added

- Graph validator: **`strategy`**, **`edges.wire`** key coverage, entity wire-code guard; **`strategy: id`** requires `wire.base === products.id`.
- Docs: wire resolution sequence in [resolution.md](docs/resolution.md); adapter ownership in [identity.md](docs/identity.md).

## [0.4.1] - 2026-07-05

Release since **v0.3.1**: multi-provider bundle layout, **`policy/markets.json`**, delivery/indemnity resolution contract, and npm publish tarball checks for the new paths.

### Fixed

- **PyPI:** PEP 639 `license = "Apache-2.0"` + `license-files` (removed invalid `License ::` classifier).
- **npm:** Exclude `docs/` from published tarball.
- **JSON:** Store UTF-8 literals instead of `\u` escapes in catalog files.

### Added

**Multi-provider catalog**

- **`graph.edges.marks`:** Zone → mark profile resolution under **`edges`** (`products` + `marks`). Catalog in `marks.json` → `profiles[]`.
- **Mark profiles:** Measured sizes in `marks.json`; resolution via `graph.edges.marks`. See [marks.md](docs/marks.md).
- **Operators:** Full letter catalogs for Deutsche Post, Ukrposhta, La Poste, and Swiss Post under **`providers/<id>/`**.
- **Policy:** **`policy/jurisdictions.json`**, **`policy/restrictions.json`**, **`policy/markets.json`** (DE, FR, CH, UA fiscal defaults).
- **Swiss Post:** Optional **`providers/swisspost/rules.json`** (e.g. thickness surcharge) where modeled.
- **Docs:** [docs/providers/](docs/providers/) tariff notes per operator; [resolution.md](docs/resolution.md), [template.md](docs/template.md), [porto_id.md](docs/porto_id.md), [tariffs.md](docs/tariffs.md); [id.md](docs/id.md), [policy.md](docs/policy.md), [formats.md](docs/formats.md).
- **Mappings:** Required provider template schemas enforced in mappings validation.

**Validation**

- **`porto validate --type porto_ids`** — enum checks, native-id cross-file refs, duplicate `porto_id` warnings.
- **`porto validate --type markets`** — registry ↔ markets coverage and fiscal shape checks.
- **`porto validate --type delivery`** — zone coverage, span/days shape, Swiss Post A/B weekday rules, feature refs, La Poste indemnity rules, twin resolution fingerprint guard.

**Delivery & resolution contract**

- **`markets.working_days`:** Per-country postal calendar (`weekdays`, `exclude_public_holidays`) on every market row.
- **`products.delivery[]`:** Zone-grouped operator delivery SLA (`span`, `days_min`/`days_max`, optional `weekdays` override). Union of entry zones must equal `product.zones`.
- **`products.included_features[]`:** Optional bundled capability ids (refs provider `features.json`; omit when not applicable).
- **`products.indemnity`:** Optional operator tier + loss/damage cap (`tier`, `max.amount` in market minor units; currency from `markets[country]`).

### Changed

**Multi-provider & docs**

- **Ukrposhta docs:** Letters-only bundle scope; verification **verified** for in-scope letter products; `porto_id` **`large`** = domestic `dokument` documented in [id.md](docs/id.md), [resolution.md](docs/resolution.md), [providers/ukrposhta.md](docs/providers/ukrposhta.md).
- **Mark layout data model:** Removed `marks.zones` and top-level `mark_edges`. Resolution lives in **`graph.edges.marks`**; `marks.json` is catalog only.
- **Marks `scope_notes`:** DE sizes flagged as sample-based; CH/FR registered documented as same footprint as lane until measured.
- **Docs:** `marks.md`, `resolution.md`, `identity.md`, `template.md` — data vs SDK split.
- **Validation order:** schema → mappings → **markets** → limits → **porto_ids** → **delivery** → graph.
- **`porto_ids.schema.json`:** Validator rejects **product** enum overlap with **service** or **feature** tokens; products are size buckets only.
- **`metadata.json`:** Generated with 2-space indent (matches data JSON).
- **2026 tariff snapshot:** Catalog baseline **`effective_from`: `2026-01-01`** on products and price rows where applicable (see per-provider docs under **`docs/providers/`**).

**Delivery contract**

- **La Poste:** Populated **`indemnity`** and **`included_features`** on recommandée and tracked letter products.
- **`products.indemnity.max`:** Amount only — currency resolved from **`markets[country].currency`** (not duplicated on product rows).

### Breaking

**Multi-provider layout**

- **Layout geometry (`formats/layouts.json`):** Removed **`address_area`** and **`print_area`**. Layout rows expose factual **`window`** and **`post_mark`** only; sender/recipient placement and printable regions are compose-layer concerns, not catalog fields.
- **Multi-provider layout:** Shared data under **`porto_data/policy/`** (restrictions, jurisdictions, **markets**) and **`porto_data/formats/`** (envelopes, layouts). Per-operator catalogs under **`porto_data/providers/<id>/`**. Root **`providers.json`** is the domain registry. Legacy flat **`porto_data/data/`** and **`data_links.json`** are removed.
- **Prices:** **`providers/<id>/prices.json`** → **`prices/products.json`** (`product_prices`) and **`prices/services.json`** (`service_prices`).
- **Weights:** **`weight_tiers.json`** → **`weights.json`**.
- **Products:** **`supported_zones`** → **`zones`**; physical sizes via **`envelope_ids`** + **`formats/envelopes.json`**; product **`unit`** is **`weight`** (`g`) only.
- **Features:** Operator-scoped **`providers/<id>/features.json`** only (no global features file).
- **Registry:** Four operators — **`deutschepost`**, **`ukrposhta`**, **`laposte`**, **`swisspost`** — in **`providers.json`** and **`mappings.json`**; keys must match **`providers/<id>/`** folder names. Registry **`label`** = display name; **`name`** = legal entity (replaces former display **`name`** + **`legal_name`**).
- **`graph.json`:** Removed **`lookup_rules`**, **`global_settings`**, and **`price_lookup`**. **`services`** is top-level. Price paths from **`dependencies`**; join keys from price schemas (`product_id`, `zone`, `weight_tier` / `service_id`).
- **Mark profile ids:** Provider-specific stamp ids (`internetmarke_*`, `mtel_*`, `webstamp_*`, `label_default`) replaced by shared layout ids (`domestic`, `international`, `registered`, `registered_international`) — not the same namespace as `porto_id: registered`. See [marks.md](docs/marks.md).

**Identity & fiscal**

- **Product `porto_id`:** Size buckets only (`small` … `extra_large`, `postcard`). La Poste recommandée rows use **`small`** like other letter products; **`registered`** is service-only (removed from product enum).
- **`porto_id` contract:** Enum-locked in **`schemas/porto_ids.schema.json`**. **`products.porto_id`** required on every product row.
- **Ukrposhta native ids:** `letter_standard` → **`lyst_standartnyi`**, `ukrposhta_document` → **`dokument`**.
- **Service refs:** Graph and prices use native **`services[].id`** only (not `porto_id` in graph **`services`** or `service_id`).
- **`policy/markets.json`:** Country-level **currency**, **VAT**, and **`international_currency`**. **`providers.json`** no longer carries `vat`.
- **Currency resolution:** SDK default is **`markets[country].currency`** (`row.currency` → file `unit.currency` → market).
- **Field names (shorter keys):** `available_services` → **`services`** (graph); `compliance_frameworks` → **`frameworks`** (limits); `integration_supported` → **`integrations`** (services); `provider_context`/`national_policy` → **`context`**/**`national`**; `intl_currencies` → **`international_currency`**; `exempt_letters` → **`exempt`** (under `vat`); top-level `vat.inclusive` / `intl_excl` → **`vat.domestic.inclusive`** / **`vat.international.inclusive`**; Porto-assigned native ids: **`recommended_international`** (not `_intl`); `metric_band_attach_service` → **`band_attach`** (rules); `severely_restricted` → **`severe`**; `disputed_territory` → **`disputed`**; `legal_reference` → **`reference`** (limits); `effective_partial` → **`partial`**; framework types `operational_*` → **`infrastructure`**/**`political`**/**`conflict`**.

**Catalog & CLI**

- **La Poste catalog:** **`lettre_recommandee_inter_r_deux`** removed (international R2 retired **2026-04-01**).
- **CLI:** **`porto validate --type products_delivery`** removed; use **`--type delivery`**.

## [0.3.1]

### Changed

- Package metadata for PyPI/npm was expanded for better registry indexing and discoverability:
    - PyPI: explicit `license` file mapping, MIT classifier, project URLs, and changelog URL in `pyproject.toml`.
    - npm: added `author`, `homepage`, `bugs`, and included `CHANGELOG.md` in published `files`.
- `bump2version` auto-tagging is disabled (`tag = False`) to avoid creating tags from release branches; tags are now intended to be created manually on `main`.
- MIT `LICENSE` text was normalized to canonical ASCII quotes for tool/scanner compatibility.

## [0.3.0] - 2026-03-06

### Changed

- **BREAKING**: Python baseline is now **3.13+** (`requires-python >=3.13`).
- **Tooling**: Ruff/MyPy targets are aligned to Python **3.13**.
- **npm runtime**: minimum Node.js is now **>=20** via `engines.node`.
- **TypeScript**: development/build baseline is now pinned to **5.9.x** (`~5.9.3`).
- **Pre-commit**: Ruff hook updated to a modern version that supports `py313`.

## [0.2.1] - 2026-03-01

### Added

- **npm**: `index.js` (main entry) and `index.d.ts` (TypeScript types) so the package has a valid entry point and typed exports; fixes registry EntryPointError.
- **PyPI**: `porto_data` package now exposes `metadata`, `__version__`, and `get_package_root()`; added `py.typed` (PEP 561) for type checkers.
- **Pre-publish test**: `tests/test_publish.sh` packs the npm tarball and builds the PyPI wheel, installs both and verifies imports; run via `make test-publish` or in the publish workflow.

### Changed

- **Publish workflow**: Validate job now sets up Node.js and runs `tests/test_publish.sh` before build; publish is rejected if the test fails.
- **npm**: `.npmignore` documents exclusions; package contents remain controlled by `package.json` `files` (no Python in the npm package).

## [0.2.0] - 2026-02-28

### Changed

- **What we publish**: Both npm and PyPI packages now ship only data (JSON + schemas). No CLI or tools in the published packages; use the repo for validation.
- **npm**: Publish uses Trusted Publishing (OIDC). No `NPM_TOKEN` secret; Node 22 and `--provenance` in CI.
- **Re-publish**: Manual workflow run lets you choose target `both`, `npm`, or `pypi` (e.g. re-publish only PyPI after a failure).
- **Versioning**: bump2version creates tag `v{new_version}` so the release workflow runs on tag push.

## [0.1.0] - 2025-12-21

### Added

- Unified `porto` CLI command (replaces standalone Python scripts)
- New CLI subcommands:
    - `porto validate` - Validate JSON schemas and data links
    - `porto validate --type schema` - Validate JSON against schemas
    - `porto validate --type links` - Validate data_links.json consistency
    - `porto validate --type links --analyze` - Detailed links analysis
    - `porto metadata` - Generate metadata.json with checksums
- Comprehensive test suite (107 tests, 87% coverage)
- Codecov integration for coverage tracking
- Test coverage reporting in CI/CD pipeline
- `scripts/validators/` package with modular validation architecture
- `scripts/data_files.py` - Centralized data file management
- Type-safe validation results with `ValidationResults` TypedDict
- Shared validation helpers in `scripts/validators/helpers.py`

### Changed

- **BREAKING**: All imports now use proper `scripts.*` package paths
    - Old: `from validators.links import ...`
    - New: `from scripts.validators.links import ...`
- Refactored validation logic into organized modules:
    - `scripts/validators/schema.py` - JSON schema validation
    - `scripts/validators/links.py` - Data links validation
    - `scripts/validators/base.py` - Type definitions
- Removed `sys.path` hacks in favor of proper package imports (full IDE support)
- Pre-commit hooks now format test files (`tests/`) and `metadata.json`
- Improved error messages and validation output
- CLI version now reads from package metadata (single source of truth)

### Technical

- Modular validation architecture with clear separation of concerns
- All imports resolvable by IDEs (syntax highlighting works)
- Removed E402 lint exceptions (no longer needed)
- Updated type checking to include both `scripts/` and `cli/` directories
- Centralized path constants in `scripts/data_files.py`
- Fail-fast validation of required entities at import time
- Improved test fixtures and utilities in `tests/conftest.py`

### Fixed

- IDE syntax highlighting for all imports
- Type checking errors with proper package imports
- Pre-commit hooks now catch formatting issues in test files
- `metadata.json` now automatically formatted on commit

## [0.0.1] - 2025-10-22

### Added

- Initial release of Porto Data v0.0.1
- 9 JSON data files with comprehensive Deutsche Post shipping data
- Complete JSON schemas for all data files
- Automated validation and quality checks
- GitHub Actions CI/CD workflow
- Pre-commit hooks for code quality
- Documentation and examples

### Data Files

- `products.json` - Shipping products (letters, merchandise)
- `services.json` - Additional services (registered mail, insurance)
- `prices.json` - Pricing tables by product, zone, and weight
- `zones.json` - Geographic zones and country mappings
- `weight_tiers.json` - Weight brackets for pricing
- `dimensions.json` - Size limits and specifications
- `restrictions.json` - Shipping restrictions and compliance frameworks
- `features.json` - Service features with German/English names
- `data_links.json` - Cross-references between data files

### Technical

- Python 3.11+ support
- JSON schema validation
- Automated metadata generation with checksums
- Ruff
- MyPy

### Fixed

- MyPy type checking issues
