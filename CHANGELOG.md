# Changelog

All notable changes to this project will be documented in this file.

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
