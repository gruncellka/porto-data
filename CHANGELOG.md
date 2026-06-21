# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Breaking

- **Multi-provider layout:** Shared data under **`porto_data/policy/`** (restrictions, jurisdictions, **markets**) and **`porto_data/formats/`** (envelopes, layouts). Per-operator catalogs under **`porto_data/providers/<id>/`**. Root **`providers.json`** is the domain registry. Legacy flat **`porto_data/data/`** and **`data_links.json`** are removed.
- **Prices:** **`providers/<id>/prices.json`** → **`prices/products.json`** (`product_prices`) and **`prices/services.json`** (`service_prices`).
- **Weights:** **`weight_tiers.json`** → **`weights.json`**.
- **Products:** **`supported_zones`** → **`zones`**; physical sizes via **`envelope_ids`** + **`formats/envelopes.json`**; product **`unit`** is **`weight`** (`g`) only.
- **Features:** Operator-scoped **`providers/<id>/features.json`** only (no global features file).
- **Registry:** Four operators — **`deutschepost`**, **`ukrposhta`**, **`laposte`**, **`swisspost`** — in **`providers.json`** and **`mappings.json`**; keys must match **`providers/<id>/`** folder names.
- **`graph.json`:** Removed **`lookup_rules`**, **`global_settings`**, and **`price_lookup`**. **`services`** is top-level. Price paths from **`dependencies`**; join keys from price schemas (`product_id`, `zone`, `weight_tier` / `service_id`).
- **`porto_id` contract:** Enum-locked in **`schemas/porto_ids.schema.json`**. **`products.porto_id`** required on every product row.
- **Ukrposhta native ids:** `letter_standard` → **`lyst_standartnyi`**, `ukrposhta_document` → **`dokument`**.
- **Service refs:** Graph and prices use native **`services[].id`** only (not `porto_id` in graph **`services`** or `service_id`).
- **`policy/markets.json`:** Country-level **currency**, **VAT**, and **`intl_ccy`**. **`providers.json`** no longer carries `vat`.
- **Currency resolution:** SDK default is **`markets[country].currency`** (`row.currency` → file `unit.currency` → market).
- **Field names (shorter keys):** `available_services` → **`services`** (graph); `compliance_frameworks` → **`frameworks`** (limits); `integration_supported` → **`integrations`** (services); `provider_context`/`national_policy` → **`context`**/**`national`**; `intl_currencies` → **`intl_ccy`**; `exempt_letters`/`intl_exclusive` → **`exempt`**/**`intl_excl`** (under `vat`); `metric_band_attach_service` → **`band_attach`** (rules); `severely_restricted` → **`severe`**; `disputed_territory` → **`disputed`**; `legal_reference` → **`reference`** (limits); `effective_partial` → **`partial`**; framework types `operational_*` → **`infrastructure`**/**`political`**/**`conflict`**.

### Added

- **Operators:** Full letter catalogs for Deutsche Post, Ukrposhta, La Poste, and Swiss Post under **`providers/<id>/`**.
- **Policy:** **`policy/jurisdictions.json`**, **`policy/restrictions.json`**, **`policy/markets.json`** (DE, FR, CH, UA fiscal defaults).
- **Swiss Post:** Optional **`providers/swisspost/rules.json`** (e.g. thickness surcharge) where modeled.
- **Validation:** **`porto validate --type porto_ids`** — enum checks, native-id cross-file refs, duplicate `porto_id` warnings.
- **Validation:** **`porto validate --type markets`** — registry ↔ markets coverage and fiscal shape checks.
- **Docs:** [docs/providers/](docs/providers/) tariff notes per operator; [resolution.md](docs/resolution.md), [provider-template.md](docs/provider-template.md), [porto_id.md](docs/porto_id.md), [tariff-verification.md](docs/tariff-verification.md); [id.md](docs/id.md), [policy.md](docs/policy.md), [formats.md](docs/formats.md).
- **Mappings:** Required provider template schemas enforced in mappings validation.

### Changed

- **Validation order:** schema → mappings → **markets** → limits → **porto_ids** → graph.
- **`metadata.json`:** Generated with 2-space indent (matches data JSON).
- **2026 tariff snapshot:** Catalog baseline **`effective_from`: `2026-01-01`** on products and price rows where applicable (see per-provider docs under **`docs/providers/`**).

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
