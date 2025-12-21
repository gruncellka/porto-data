# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2025-12-21

### Added

-   Unified `porto` CLI command (replaces standalone Python scripts)
-   New CLI subcommands:
    -   `porto validate` - Validate JSON schemas and data links
    -   `porto validate --type schema` - Validate JSON against schemas
    -   `porto validate --type links` - Validate data_links.json consistency
    -   `porto validate --type links --analyze` - Detailed links analysis
    -   `porto metadata` - Generate metadata.json with checksums
-   Comprehensive test suite (107 tests, 87% coverage)
-   Codecov integration for coverage tracking
-   Test coverage reporting in CI/CD pipeline
-   `scripts/validators/` package with modular validation architecture
-   `scripts/data_files.py` - Centralized data file management
-   Type-safe validation results with `ValidationResults` TypedDict
-   Shared validation helpers in `scripts/validators/helpers.py`

### Changed

-   **BREAKING**: All imports now use proper `scripts.*` package paths
    -   Old: `from validators.links import ...`
    -   New: `from scripts.validators.links import ...`
-   Refactored validation logic into organized modules:
    -   `scripts/validators/schema.py` - JSON schema validation
    -   `scripts/validators/links.py` - Data links validation
    -   `scripts/validators/base.py` - Type definitions
-   Removed `sys.path` hacks in favor of proper package imports (full IDE support)
-   Pre-commit hooks now format test files (`tests/`) and `metadata.json`
-   Improved error messages and validation output
-   CLI version now reads from package metadata (single source of truth)

### Technical

-   Modular validation architecture with clear separation of concerns
-   All imports resolvable by IDEs (syntax highlighting works)
-   Removed E402 lint exceptions (no longer needed)
-   Updated type checking to include both `scripts/` and `cli/` directories
-   Centralized path constants in `scripts/data_files.py`
-   Fail-fast validation of required entities at import time
-   Improved test fixtures and utilities in `tests/conftest.py`

### Fixed

-   IDE syntax highlighting for all imports
-   Type checking errors with proper package imports
-   Pre-commit hooks now catch formatting issues in test files
-   `metadata.json` now automatically formatted on commit

## [0.0.1] - 2025-10-22

### Added

-   Initial release of Porto Data v0.0.1
-   9 JSON data files with comprehensive Deutsche Post shipping data
-   Complete JSON schemas for all data files
-   Automated validation and quality checks
-   GitHub Actions CI/CD workflow
-   Pre-commit hooks for code quality
-   Documentation and examples

### Data Files

-   `products.json` - Shipping products (letters, merchandise)
-   `services.json` - Additional services (registered mail, insurance)
-   `prices.json` - Pricing tables by product, zone, and weight
-   `zones.json` - Geographic zones and country mappings
-   `weight_tiers.json` - Weight brackets for pricing
-   `dimensions.json` - Size limits and specifications
-   `restrictions.json` - Shipping restrictions and compliance frameworks
-   `features.json` - Service features with German/English names
-   `data_links.json` - Cross-references between data files

### Technical

-   Python 3.11+ support
-   JSON schema validation
-   Automated metadata generation with checksums
-   Ruff
-   MyPy

### Fixed

-   MyPy type checking issues
