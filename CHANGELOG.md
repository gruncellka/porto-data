# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### BREAKING

- **Data layout:** The single flat bundle **`porto_data/data/*.json`** is removed. Data now lives under **`porto_data/global/`** (shared across providers) and **`porto_data/providers/<provider_id>/`** (per operator). Tooling and SDKs must resolve paths via **`mappings.json`** and **`metadata.json`**—do not assume legacy paths such as `porto_data/data/products.json`.
- **`data_links.json` / `data_links.schema.json` removed.** Cross-file dependencies, product **links**, **lookup_rules**, and **global_settings** are defined only in each provider’s **`graph.json`**, validated by **`schemas/graph.schema.json`**, with **`file_type`: `graph`**. (Previously named **`resolution_graph`** / **`resolution_graph.schema.json`** / `file_type`: `resolution_graph`.)
- **Provider registry:** **`global/providers.json`** is authoritative for which provider ids exist. Directory names under **`providers/`** and keys in **`mappings.json`** must match that registry.
- **Jurisdictions reference:** **`global/jurisdictions.json`** must use **`file_type`: `jurisdictions`** and a top-level **`jurisdictions`** object with keys **`eu`** and **`un`** (ISO 3166-1 alpha-2 member lists; same tokens as symbolic **`EU`** / **`UN`** jurisdiction). Older shapes (**`countries`**, **`jurisdiction_reference`** `file_type`, top-level **`groups`**, or legacy **`eu_member_states`** / **`un_member_states`**) are not supported by current porto-data contracts or downstream loaders.
- **Features catalog:** **`global/features.json` removed.** Feature definitions live under **`providers/<provider_id>/features.json`** (same resolution pattern as products/services). Each file lists only ids that operator supports; **`name`** is operator-native text, **`label`** is English for unified tooling. **`provider`** on the document is required. Loaders resolve via **`mappings.json`** / **`metadata.json`**—do not assume a global features path.

### Added

- **`global/providers.json`** + **`schemas/providers.schema.json`** — provider ids, display metadata, optional IANA **`timezone`** (operational calendar for prices/services/limits where row-level timezone is absent).
- **`global/jurisdictions.json`** + **`schemas/jurisdictions.schema.json`** — EU/UN ISO 3166-1 alpha-2 lists under **`jurisdictions.eu`** and **`jurisdictions.un`**; **`unit`** documents encodings. Regenerate via **`scripts/generate_countries_reference.py`**.
- **`providers/<id>/limits.json`** + **`schemas/limits.schema.json`** — operator **operational** limits (conflict, infrastructure, internal policy) and **`compliance_frameworks`** with required framework **`timezone`** (must match **`global/providers.json`** for that provider). SDKs merge limits with global **`restrictions.json`** in one restriction surface.
- **`providers/<id>/graph.json`** + **`schemas/graph.schema.json`** — dependency DAG, **links** (product × zone × weight_tier), **lookup_rules**, **global_settings** (e.g. **available_services**). All providers in **`mappings.json`** declare **`jurisdictions.json`** and **`limits`** (may be empty) in **dependencies** so load order is consistent.
- **Multi-provider datasets** in repo layout: **`deutschepost`**, **`swisspost`**, **`laposte`** (per **`mappings.json`**); Swiss Post and La Poste ship minimal/empty **limits** where applicable.
- **Validation:** **`porto validate --type registry`** and **`scripts/validators/providers_registry.py`** — checks **`global/providers.json`** vs provider folders, **mappings**, and **metadata** manifest.
- **Scripts:** **`scripts/format_json_file.py`**; **`scripts/generate_countries_reference.py`** for **jurisdictions** payloads.
- **Tests:** provider registry, countries/jurisdictions generator, execution-semantics coverage, expanded **`test_data_files`** for mappings-driven paths.

### Changed

- **`services.json`:** **`porto_id`** (unified semantic), **`label`**, provider **`id`**, native **`name`**. Deutsche Post **`id`** e.g. `einschreiben` / `einschreiben_einwurf` with **`porto_id`** `registered_mail` / `registered_mail_mailbox`; Swiss **`a_mail_plus`** / La Poste **`suivi`** share **`porto_id`** `letter_tracking`. **Graph `available_services`** and **`prices.service_id`** use **native `id`** only (mailbox row was aligned from legacy `registered_mail_mailbox`); SDK **`get_service_price`** accepts **`id`** or **`porto_id`**. Validation still allows either token where references are resolved.
- **Swiss Post `products.json`:** provider **`id`** values renamed for clarity (`letter_a_post_*`, `letter_b_post_*`, `letter_international_*`); **`porto_id`** unchanged for cross-provider resolution. **`graph.json` `links`** and **`prices.json` `product_id`** updated to match.
- **Features (`providers/*/features.json`):** provider-scoped **`id`** (e.g. `sendungsnummer`, `einliefernachweis`, `numero_suivi`) distinct from unified **`porto_id`**; **`services[].features`** may still list **`porto_id`** strings (cross-file validation accepts either).
- **`products.json` `unit`:** **`dimension` removed**; only **`weight`** (`g`) remains. Envelope/format semantics stay on **`dimension_ids`** + **`global/dimensions.json`** (linear **mm** there). Graph **`validate_dimension_units`** compares **graph** and **dimensions** only.
- **`limits.json`:** optional top-level **`operator_context`** renamed to **`provider_context`** (aligns with `provider` id and “provider limits” wording).
- **Features catalog:** each feature row requires **`porto_id`** (unified Porto capability id, stable across providers) alongside **`id`** (provider-scoped key in that file). **`services[].features`** may reference either **`id`** or **`porto_id`**. SDK cross-file validation and feature lookup accept both.
- **`products.schema.json` `porto_id` description** — documents why **`porto_id`** often matches **`id`** for some operators and differs for others.
- **`jurisdictions` membership keys:** **`eu`** / **`un`** replace **`eu_member_states`** / **`un_member_states`** so data keys match symbolic **`EU`** / **`UN`** jurisdiction tokens for resolvers.
- **`metadata.json`** — generated for **global** + **per-provider** entities (paths, checksums, schema URLs). Entity keys align with logical names (**`graph`**, **`jurisdictions`**, **`limits`**, …).
- **`scripts/data_files.py`** — resolves file names and paths from **`mappings.json`**; constants such as **`GRAPH_FILE`**; provider-aware **`get_data_file_path`**; required-entity checks tied to mappings.
- **Graph validation** — class **`GraphValidator`**, entrypoint **`validate_graph`**; Makefile target **`validate-graph`**; pre-commit hook **`validate-graph`** (triggers on **`graph.json`** and core provider data files). Deprecated aliases **`ResolutionGraphValidator`** / **`validate_resolution_graph`** remain in **`scripts.validators.links`** for one release cycle.
- **`global/restrictions.json` / `schemas/restrictions.schema.json`** — legal/sanctions-style rows only; **`compliance_frameworks`** are metadata (**`jurisdiction`**, scope, **`legal_reference`**, optional **`timezone`** for row **effective\_\*** interpretation). **Framework-level `effective_from` / `effective_to` removed** from global restrictions (activation is **row-level** only). Removed top-level **`denied_party_screening`** and related **`sources`** noise. **`applicability`** / operator pseudo-jurisdiction **`DP`** removed; operator rules live under **`limits.json`** only. **`jurisdiction`** values use **`pattern: ^[A-Z]{2}$`** (blocs and states) instead of a closed enum.
- **`SANCTIONS_VE` (and similar):** **`jurisdiction`** expressed as **`EU`** where EU-only; timezone on frameworks is a **calendar anchor**, not jurisdiction.
- **Deutsche Post operational** restrictions/frameworks that previously lived under global **`applicability.providers`** moved to **`providers/deutschepost/limits.json`**.
- **`sanctions_information`:** removed optional **`de_national_postal_law`** and framework **`POSTG_8`** (not destination-verifiable for letter checks); **`provider_context`** in **limits** (formerly `operator_context`) updated accordingly.
- **Shared schemas** (**`dimensions`**, **`features`**, **`prices`**, **`products`**, **`services`**, **`weight_tiers`**, **`zones`**) — revised for execution fields (**`mark_type`**, **`tracking_mode`**), effective dating, and multi-provider consistency where applicable.
- **`README.md`** — documents **global** vs **providers**, **jurisdictions**, **graph**, **limits**, registry, and standards (jurisdiction vs timezone).
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
- `providers/<id>/features.json` - Supported service features (stable ids; native `name`, English `label`)
- `data_links.json` - Cross-references between data files

### Technical

- Python 3.11+ support
- JSON schema validation
- Automated metadata generation with checksums
- Ruff
- MyPy

### Fixed

- MyPy type checking issues
