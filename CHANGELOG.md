# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Changed

- **Shared bundle layout (BREAKING):** **`porto_data/global/policy/*`** and **`porto_data/global/mails/*`** are now **`porto_data/policy/*`** and **`porto_data/mails/*`** at bundle root (no **`global/`** folder for these files). **`mappings.json`**, provider **`graph.json`**, **`metadata.json`**, and SDK loaders updated; legacy paths **`global/policy/...`** and **`global/mails/...`** remain supported as fallbacks in SDKs where applicable.

- **Envelope layouts file (BREAKING):** **`global/envelope_layouts.json` → `mails/layouts.json`**. **`mappings.json`**, provider **`graph.json`**, and **`metadata.json`** updated; schema now **`schemas/layouts.schema.json`** (`file_type` in JSON now **`layouts`**).

- **Envelope layouts (BREAKING):** Row field **`source` → `standard`** (compact norm id, e.g. **`DIN678`**, **`SN010130`**, **`NFEN13850`**). Removed **`inherit_from`**; **CH** and **FR** define full **`layout`** blocks. **DE** = DIN 678 geometry; **CH** cites Swiss **SN 010 130**; **FR** cites **NF EN 13850** (window envelopes). Current **mm** values align with harmonized ISO/DL/C layouts used for mechanised mail; adjust per operator PDFs if a national spec differs.

- **Documentation:** Removed **`docs/TARIFF_EFFECTIVE_DATES_RESEARCH.md`**. **`effective_from`: `2026-01-01`** on provider products and prices is documented as the **2026** catalog baseline in **[`README.md`](README.md)** only.

- **Products (BREAKING):** Renamed **`supported_zones` → `zones`** in **`products.json`** (schema **`products.schema.json`**). **`services.json`** still uses **`supported_zones`** for per-service API zone restrictions.
- **`provider_rules`:** Removed **`zones`** from rule rows; effective zone scope is the resolved **`product_id`** plus **`graph.edges`** / product **`zones`** (no duplicate zone list on rules).
- **`provider_rules`:** Top-level **`unit`** (e.g. **`thickness`**: **`mm`**) defines measurement units; rule **`metric`** uses short names (**`thickness`**, not `thickness_mm`). Validators require **`unit.thickness`** **`mm`** when **`metric`** is **`thickness`**.

- **Envelope layouts (BREAKING):** Removed **`porto_data/envelopes/`** and related schemas. **New** **`global/layouts.json`** (`file_type` **`layouts`**) — jurisdictions **DE**, **CH**, **FR**, **`envelopes.<id>`** rows with **`orientation`**, **`layout`**, optional **`standard`**. Validators enforce address/window rules. Provider **`graph.json`** lists **`global/layouts.json`** (depends on **`envelopes.json`**).
- **Prices (BREAKING):** Replaced **`providers/<id>/prices.json`** with **`providers/<id>/prices/products.json`** (`file_type` **`product_prices`**) and **`providers/<id>/prices/services.json`** (`file_type` **`service_prices`**). JSON keys remain **`product_prices`** / **`service_prices`**; schemas **`product_prices.schema.json`**, **`service_prices.schema.json`**. **`graph.json`** uses provider-relative paths (e.g. **`prices/products.json`**) and **`global/...`** for shared files; **`global_settings.price_lookup`** matches those paths.
- **`mappings.json`:** Dropped **`envelopes`** block; shared maps **`layouts.schema.json`** → **`mails/layouts.json`**.
- **`global/envelopes.json` `sheets[]`:** Extended **C6** with **A5 + half**; **C4** with **A5** and **B5** flat; **B4** with **A5** and **B5** flat so common ISO 216 preparations for the same five envelope ids are listed without a separate `sheets.json`.

- **`global/envelopes.json` field renames (BREAKING):** **`typical_document` → `sheets`**, **`iso_sheet` → `sheet`**, **`standard_reference` → `standard`** (value still **`ISO269`**).

- **`sheets[].fold`:** Canonical enum is **`flat` \| `half` \| `quarter` \| `trifold`** (outcome-oriented: flat sheet, halved, quartered area for small envelope, letter trifold / DL). Replaces **`none` → `flat`**, **`two_fold` → `quarter`**, **`thirds` → `trifold`**. **BREAKING** for loaders using the previous fold tokens.

- **`global/envelopes.json`:** Catalog trimmed to **DL, C6, C5, C4, B4** (aligned with modeled FR/CH/DE letter products). **`standard`** is the constant **`ISO269`** (maps semantically to **`envelope_standards.standard_id` `iso_269`**). Each row includes **`sheets[]`**: **`sheet`** (ISO 216, e.g. A4) + **`fold`** (`flat` \| `half` \| `quarter` \| `trifold`) plus optional **`description`**. **`envelopes/standard_layouts.json`** DIN 678 layouts removed for formats no longer in the catalog (C8, C7, B6, B5, C3).

- **Envelopes (BREAKING for loaders):** Replaced monolithic **`envelopes/envelopes.json`** with **`global/envelopes.json`** (canonical envelope **`id`**, **`width`/`height`**, **`standard`** e.g. ISO 269; root array **`envelopes`**), **`envelopes/envelope_standards.json`** (international vs national standards registry), and **`envelopes/standard_layouts.json`** (layout per **`standard_id` + `format_id`**, e.g. DIN 678). **`envelope_rules.json`** adds **`layout_resolution`** (`default_standard_id`, **`by_profile_id`**). **`products.envelope_ids`** reference the same **`id`** values as rows in **`global/envelopes.json`**. Provider **`graph.json`** **`dependencies`** entry **`envelopes`** points at **`envelopes.json`** (global file name under **`porto_data/global/`**), alongside **`envelope_standards.json`**, **`standard_layouts.json`**. \*(Earlier drafts used **`global/envelope_formats.json`** / **`formats[]`** / schema **`envelope_formats`** — migrated to **`envelopes.json`** / **`envelopes[]`** / **`schemas/envelopes.schema.json`**.)

### Added

- **`docs/providers/`** — per-operator official tariff reference markdown: **`deutschepost.md`**, **`laposte.md`**, **`swisspost.md`** (links, snapshot tables, `porto_data` expectations). Consumers in the Lab monorepo: see root **`docs/README.md`** for an index that links here.

- **Unified `porto_id` documentation:** canonical naming policy in **`docs/id.md`**; per-provider **`id` / `native_id` / `porto_id`** tables in repo-root **`PORTO_ID_MAPPING.md`**; migration notes in **`porto_id_normalization_plan.md`**. These three files cross-link each other; **`README.md`** lists them under Related resources.

### Changed (provider tariffs 2026 alignment)

- **Deutsche Post:** Added **`postkarte`** (W0020, **95** / **125** cents domestic/international) aligned with official Postkarte = Standard letter postage; **`graph.json`** description documents parity with **`docs/providers/deutschepost.md`** tables.
- **Deutsche Post:** International **Brief** prices use one **worldwide** ladder (same cents for `zone_1_eu`, `zone_2_europe`, `world`) per deutschepost.de _Alle Länder – ein Preis – weltweit_; added **`maxibrief_international_heavy`** (W2000, abroad only, **17,00 €**); domestic/international letter rows use **`effective_from`: `2026-01-01`**. **`einschreiben`** / **`zusatzversicherung`** `supported_zones` include **`zone_2_europe`**.
- **Swiss Post:** Removed **`a_post_midibrief`** / **`b_post_midibrief`** (DigitalStamp model is standard vs large only); domestic **Standardbrief** envelopes **DL, C6** only; international **`zone_1_eu`** and **`world`** share the same document-letter amounts as on post.ch; **`effective_from`: `2026-01-01`**.
- **La Poste:** Replaced legacy **`lettre_prioritaire_*`** with official letter lines: **`lettre_verte`**, **`lettre_verte_suivie`**, **`lettre_services_plus`**, **`lettre_recommandee_*`**, **`lettre_recommandee_inter_*`**; weight tiers **W0020–W2000** (plus **W0050** for recommandée); prices from laposte.fr **2026** tables; services **`suivi_option`** (optional tracking for Lettre verte), **`avis_de_reception_*`** for recommandée AR add-ons.

### BREAKING

- **Data layout:** The single flat bundle **`porto_data/data/*.json`** is removed. Data now lives under **`porto_data/global/`** (shared across providers) and **`porto_data/providers/<provider_id>/`** (per operator). Tooling and SDKs must resolve paths via **`mappings.json`** and **`metadata.json`**—do not assume legacy paths such as `porto_data/data/products.json`.
- **`data_links.json` / `data_links.schema.json` removed.** Cross-file dependencies, product **edges** (zones × weight tiers), **lookup_rules**, and **global_settings** are defined only in each provider’s **`graph.json`**, validated by **`schemas/graph.schema.json`**, with **`file_type`: `graph`**. (Previously named **`resolution_graph`** / **`resolution_graph.schema.json`** / `file_type`: `resolution_graph`.)
- **Provider registry:** **`providers.json`** is authoritative for which provider ids exist. Directory names under **`providers/`** and keys in **`mappings.json`** must match that registry.
- **Jurisdictions reference:** **`policy/jurisdictions.json`** must use **`file_type`: `jurisdictions`** and a top-level **`jurisdictions`** object with keys **`eu`** and **`un`** (ISO 3166-1 alpha-2 member lists; same tokens as symbolic **`EU`** / **`UN`** jurisdiction). Older shapes (**`countries`**, **`jurisdiction_reference`** `file_type`, top-level **`groups`**, or legacy **`eu_member_states`** / **`un_member_states`**) are not supported by current porto-data contracts or downstream loaders.
- **Features catalog:** **`global/features.json` removed.** Feature definitions live under **`providers/<provider_id>/features.json`** (same resolution pattern as products/services). Each file lists only ids that operator supports; **`name`** is operator-native text, **`label`** is English for unified tooling. **`provider`** on the document is required. Loaders resolve via **`mappings.json`** / **`metadata.json`**—do not assume a global features path.

### Added

- **`providers.json`** + **`schemas/providers.schema.json`** — provider ids, display metadata, optional IANA **`timezone`** (operational calendar for prices/services/limits where row-level timezone is absent).
- **`policy/jurisdictions.json`** + **`schemas/jurisdictions.schema.json`** — EU/UN ISO 3166-1 alpha-2 lists under **`jurisdictions.eu`** and **`jurisdictions.un`**; **`unit`** documents encodings.
- **`providers/<id>/limits.json`** + **`schemas/limits.schema.json`** — operator **operational** limits (conflict, infrastructure, internal policy) and **`compliance_frameworks`** with required framework **`timezone`** (must match **`global/providers.json`** for that provider). SDKs merge limits with global **`restrictions.json`** in one restriction surface.
- **`providers/<id>/graph.json`** + **`schemas/graph.schema.json`** — dependency DAG, **edges** (product × zone × weight_tier), **lookup_rules**, **global_settings** (e.g. **available_services**). All providers in **`mappings.json`** declare **`jurisdictions.json`** and **`limits`** (may be empty) in **dependencies** so load order is consistent.
- **Multi-provider datasets** in repo layout: **`deutschepost`**, **`swisspost`**, **`laposte`** (per **`mappings.json`**); Swiss Post and La Poste ship minimal/empty **limits** where applicable.
- **Validation:** **`porto validate --type registry`** and **`scripts/validators/providers_registry.py`** — checks **`global/providers.json`** vs provider folders, **mappings**, and **metadata** manifest.
- **Scripts:** **`scripts/format_json_file.py`**.
- **Tests:** provider registry, jurisdictions/schema coverage, execution-semantics coverage, expanded **`test_data_files`** for mappings-driven paths.

### Changed

- **`graph.json`:** top-level **`links`** renamed to **`edges`** (product → zones + weight_tiers). Schema, all providers, **`ResolutionGraph`**, and SDKs use **`edges`**.
- **Graph validator:** **`GraphValidator`** / **`validate_graph`** in **`scripts/validators/graph.py`**. **`limits_scope.py`** validates **`limits.json`** only (not graph).
- **`services.json`:** **`porto_id`** (unified semantic), **`label`**, provider **`id`**, native **`name`**. Deutsche Post **`id`** e.g. `einschreiben` / `einschreiben_einwurf` with **`porto_id`** `registered_mail` / `registered_mail_mailbox`; Swiss **`a_mail_plus`** / La Poste **`suivi`** share **`porto_id`** `letter_tracking`. **Graph `available_services`** and **`prices.service_id`** use **native `id`** only (mailbox row was aligned from legacy `registered_mail_mailbox`); SDK **`get_service_price`** accepts **`id`** or **`porto_id`**. Validation still allows either token where references are resolved.
- **Swiss Post `products.json`:** provider **`id`** values renamed for clarity (`letter_a_post_*`, `letter_b_post_*`, `letter_international_*`); **`porto_id`** unchanged for cross-provider resolution. **`graph.json` `edges`** and **`prices.json` `product_id`** updated to match.
- **Features (`providers/*/features.json`):** provider-scoped **`id`** (e.g. `sendungsnummer`, `einliefernachweis`, `numero_suivi`) distinct from unified **`porto_id`**; **`services[].features`** may still list **`porto_id`** strings (cross-file validation accepts either).
- **`products.json` `unit`:** **`dimension` removed**; only **`weight`** (`g`) remains. Envelope/format semantics stay on **`dimension_ids`** + **`global/dimensions.json`** (linear **mm** there). Graph **`validate_dimension_units`** compares **graph** and **dimensions** only.
- **`limits.json`:** optional top-level **`operator_context`** renamed to **`provider_context`** (aligns with `provider` id and “provider limits” wording).
- **Features catalog:** each feature row requires **`porto_id`** (unified Porto capability id, stable across providers) alongside **`id`** (provider-scoped key in that file). **`services[].features`** may reference either **`id`** or **`porto_id`**. SDK cross-file validation and feature lookup accept both.
- **`products.schema.json` `porto_id` description** — documents why **`porto_id`** often matches **`id`** for some operators and differs for others.
- **`jurisdictions` membership keys:** **`eu`** / **`un`** replace **`eu_member_states`** / **`un_member_states`** so data keys match symbolic **`EU`** / **`UN`** jurisdiction tokens for resolvers.
- **`metadata.json`** — generated for **global** + **per-provider** entities (paths, checksums, schema URLs). Entity keys align with logical names (**`graph`**, **`jurisdictions`**, **`limits`**, …).
- **`scripts/data_files.py`** — resolves file names and paths from **`mappings.json`**; constants such as **`GRAPH_FILE`**; provider-aware **`get_data_file_path`**; required-entity checks tied to mappings.
- **Graph validation** — class **`GraphValidator`**, entrypoint **`validate_graph`** in **`scripts/validators/graph.py`**; Makefile target **`validate-graph`**; pre-commit hook **`validate-graph`** (triggers on **`graph.json`** and core provider data files).
- **`policy/restrictions.json` / `schemas/restrictions.schema.json`** — legal/sanctions-style rows only; **`compliance_frameworks`** are metadata (**`jurisdiction`**, scope, **`legal_reference`**, optional **`timezone`** for row **effective\_\*** interpretation). **Framework-level `effective_from` / `effective_to` removed** from global restrictions (activation is **row-level** only). Removed top-level **`denied_party_screening`** and related **`sources`** noise. **`applicability`** / operator pseudo-jurisdiction **`DP`** removed; operator rules live under **`limits.json`** only. **`jurisdiction`** values use **`pattern: ^[A-Z]{2}$`** (blocs and states) instead of a closed enum.
- **`SANCTIONS_VE` (and similar):** **`jurisdiction`** expressed as **`EU`** where EU-only; timezone on frameworks is a **calendar anchor**, not jurisdiction.
- **Deutsche Post operational** restrictions/frameworks that previously lived under global **`applicability.providers`** moved to **`providers/deutschepost/limits.json`**.
- **`sanctions_information`:** removed optional **`de_national_postal_law`** and framework **`POSTG_8`** (not destination-verifiable for letter checks); **`provider_context`** in **limits** (formerly `operator_context`) updated accordingly.
- **Shared schemas** (**`dimensions`**, **`features`**, **`prices`**, **`products`**, **`services`**, **`weights`**, **`zones`**) — revised for execution fields (**`mark_type`**, **`tracking_mode`**), effective dating, and multi-provider consistency where applicable.
- **`README.md`** — documents **global** vs **providers**, **jurisdictions**, **graph**, **limits**, registry, and standards (jurisdiction vs timezone).
- **`CONTRIBUTING.md`** — paths, CLI, and Make targets match **`global/`** + **`providers/<id>/`** and **`--type graph`** (removed obsolete flat-`data/` and **`data_links`** wording).
- **Tests:** `tests/test_validate_data_links.py` renamed to **`tests/test_validate_graph.py`**.
- **Validators:** `validate_unit_consistency` parameter **`graph_unit_value`** (replacing legacy **`data_links_value`** naming); graph unit locals renamed accordingly in **`graph.py`**.
- **`LICENSE`** — full **Apache-2.0** license text.
- **Package metadata** (PyPI/npm): expanded URLs, classifiers, and published **`CHANGELOG.md`** reference where configured.

### Removed

- **`porto_data/data/`** directory and its nine legacy JSON files.
- **`data_links`** schema and data file.

### Tooling

- **Python** baseline remains **`>=3.13`** (see **[0.3.0]**).
- **`bump2version`:** `tag = False` (tags created manually on **`main`**).
- **CLI `validate`:** default run includes **schema**, **registry**, and **graph** validation.

---

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
    - `porto validate` - Validate JSON schemas and graph consistency
    - `porto validate --type schema` - Validate JSON against schemas
    - `porto validate --type graph` - Validate `graph.json` (including `edges`)
    - `porto validate --type graph --analyze` - Detailed graph analysis
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
    - Import graph validation: `from scripts.validators.graph import GraphValidator, validate_graph`
- Refactored validation logic into organized modules:
    - `scripts/validators/schema.py` - JSON schema validation
    - `scripts/validators/graph.py` - **graph.json** validation (including the `edges` object)
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
- `weights.json` - Weight brackets for pricing
- `dimensions.json` - Size limits and specifications
- `restrictions.json` - Shipping restrictions and compliance frameworks
- `providers/<id>/features.json` - Supported service features (stable ids; native `name`, English `label`)
- `graph.json` - Cross-file dependencies and product edges (per provider)

### Technical

- Python 3.11+ support
- JSON schema validation
- Automated metadata generation with checksums
- Ruff
- MyPy

### Fixed

- MyPy type checking issues
