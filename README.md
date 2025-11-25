# Porto Data

[![porto-data-validation](https://github.com/gruncellka/porto-data/actions/workflows/porto-data-validation.yml/badge.svg)](https://github.com/gruncellka/porto-data/actions/workflows/porto-data-validation.yml)

**Structured JSON data for Deutsche Post / DHL shipping services**

A comprehensive, schema-validated dataset containing Deutsche Post pricing, restrictions, zones, features, services, and compliance frameworks for international postal services with complete JSON schema validation and automated quality assurance.

---

## 🎯 Use Cases

This dataset is perfect for:

-   **E-commerce platforms** - Calculate shipping costs and restrictions
-   **Logistics software** - Integrate Deutsche Post pricing and rules
-   **Compliance tools** - Check shipping restrictions and sanctions
-   **Research projects** - Analyze postal service patterns and policies
-   **Educational purposes** - Learn about international shipping regulations

---

## 📈 Data Statistics

-   **9 JSON files** with comprehensive postal data
-   **9 JSON schemas** ensuring data integrity
-   **100+ countries** covered in shipping zones
-   **5 product types** (letters, merchandise)
-   **5 service types** (registered mail, insurance)
-   **31 restrictions** with 19 compliance frameworks

---

## 📦 What's Inside

| File                | Description                                                        |
| ------------------- | ------------------------------------------------------------------ |
| `products.json`     | Shipping products (letters, parcels, packages)                     |
| `services.json`     | Additional services (registered mail, insurance, etc.)             |
| `prices.json`       | Pricing tables by product, zone, and weight (with effective dates) |
| `zones.json`        | Geographic zones and country mappings                              |
| `weight_tiers.json` | Weight brackets for pricing                                        |
| `dimensions.json`   | Size limits and specifications                                     |
| `features.json`     | Service features and capabilities                                  |
| `restrictions.json` | Shipping restrictions, sanctions, compliance frameworks            |
| `data_links.json`   | Cross-references between data files                                |

**All data is validated against JSON schemas** in the `schemas/` directory.

---

## 🚀 Quick Start

### Prerequisites

-   Python 3.11+
-   Git

### Installation

```bash
git clone <repository-url>
cd porto-data-draft
make setup
```

This installs:

-   `jsonschema` for validation
-   `ruff`, `mypy` for code quality (Ruff handles formatting + linting)
-   `pre-commit` framework with hooks for automatic validation

### Verify Installation

```bash
make validate    # Validate all JSON files
make quality     # Run all quality checks
```

---

## 📊 Data Structure

### Products → Prices → Zones

```
Product (e.g., "letter_standard")
  ├─ has dimension_ids → dimensions.json
  ├─ has weight_tier → weight_tiers.json
  └─ has prices in zones → prices.json
       ├─ price array with effective_from/effective_to dates
       └─ references zones.json
```

### Services → Features

```
Service (e.g., "einschreiben_einwurf")
  ├─ has features → features.json
  ├─ has coverage (in cents)
  └─ applies to products → products.json
```

### Restrictions → Frameworks

```
Restriction (e.g., "YEMEN_2015")
  ├─ country_code: "YE"
  ├─ region_code: null
  └─ framework_id → compliance_frameworks
       └─ Legal basis (conflict zones, operational policies)
```

**All relationships are one-directional** (no circular dependencies).

### Data Links (Metadata)

`data_links.json` provides links about data file relationships:
- **Dependencies** - Which files depend on which
- **Links** - Product-to-zone-to-weight-tier mappings for fast lookups
- **Lookup rules** - How to find prices, services, and resolve weights
- **Global settings** - Available services and price lookup configuration

This metadata is primarily used by SDKs for optimized data access and validation, but is also useful for understanding the data structure.

---

## 📝 Common Tasks

### Viewing Data

All data files are in the `data/` directory. Open any `.json` file to view the data.

### Making Changes

```bash
# 1. Edit JSON files
vim data/products.json

# 2. Validate your changes
make validate

# 3. Format your changes
make format

# 4. Commit
git add .
git commit -m "feat: update products"
# → Pre-commit hooks run automatically and validate everything
# → If metadata.json is regenerated, commit will be rejected
# → Stage metadata.json and commit again
```

### Manual Validation

```bash
make validate      # Validate JSON against schemas
make lint-json     # Check JSON syntax only
make format-json   # Auto-format JSON files
```

---

## 🛠 Development

### Pre-Commit Hooks

The pre-commit framework **automatically** runs hooks on every commit:

1. ✅ Formats all JSON and Python files (auto-staged)
2. ✅ Validates JSON syntax
3. ✅ Validates against schemas
4. ✅ Runs Python linting and type checking
5. ✅ Regenerates metadata.json if data files changed

**Important behaviors:**

-   ✅ Modified files are automatically staged (fixes uncommitted changes bug)
-   ❌ If `metadata.json` is regenerated but not staged, commit is **rejected** - you must stage `metadata.json` in the same commit
-   ❌ If validation fails, commit is blocked until you fix the errors

**Installing hooks:**

```bash
make install-hooks  # Installs pre-commit framework hooks
```

### Available Commands

```bash
# Validation
make validate      # Validate all JSON files

# Formatting
make format        # Format JSON and Python
make format-json   # Format JSON only
make format-code   # Format Python only

# Linting
make lint          # Lint JSON and Python
make lint-json     # Lint JSON only
make lint-code     # Lint Python only

# Quality
make quality       # Run all checks (format, lint, validate, type-check)

# Metadata
make metadata      # Generate metadata.json with checksums

# Help
make help          # Show all commands
```

### About metadata.json

The `metadata.json` file is automatically generated with checksums of all data and schema files. It's regenerated when:

-   Any file in `data/` or `schemas/` changes
-   Checksums don't match the current files

**Structure:**
-   Grouped by entity name (e.g., `products`, `services`) with data and schema files linked together
-   Includes canonical schema URLs from `$id` properties
-   Each data file includes `$schema` property pointing to its schema URL

**Commit behavior:**

-   If `metadata.json` is regenerated during commit, the commit is **rejected** if `metadata.json` is not staged
-   You must stage `metadata.json` in the same commit as your data changes: `git add metadata.json`
-   This ensures `metadata.json` stays in sync with data files in the same commit

### Schema Mapping

Schema-to-data file mappings are defined in `mappings.json` (source of truth). All data files include a `$schema` property with the canonical schema URL for validation and editor support.

---

## 🌍 Standards & Compliance

### ISO Standards

-   **Country codes**: ISO 3166-1 alpha-2 (`DE`, `US`, `FR`, `YE`)
-   **Region codes**: ISO 3166-2 (`DE-BY`, `US-CA`, `FR-75`)
-   **Dates**: ISO 8601 (`2024-01-15`, `2023-06-01`)

### Jurisdiction Codes

-   `EU` - European Union
-   `UN` - United Nations
-   `DE` - Germany (national)
-   `DP` - Deutsche Post (operational)

### Restrictions Features

-   ✅ Tracks occupied/disputed territories
-   ✅ Links to legal frameworks (EU sanctions, UN resolutions)
-   ✅ Supports partial territory restrictions (`effective_partial`)
-   ✅ Historical effective dates (`effective_from`, `effective_to`)

---

## 🔍 Schema Validation

All JSON files are validated against schemas to ensure:

-   ✅ Required fields are present
-   ✅ Data types are correct (string, number, boolean, array)
-   ✅ Values match allowed enums
-   ✅ ISO codes follow correct patterns
-   ✅ Dates are properly formatted
-   ✅ Cross-references are valid

### Example Validation Error

```bash
make validate
```

---

## 📂 Project Structure

```
porto-data-draft/
├── data/                   # Main data files (JSON)
│   ├── products.json       # Includes $schema property
│   ├── services.json
│   ├── prices.json
│   ├── zones.json
│   ├── weight_tiers.json
│   ├── dimensions.json
│   ├── restrictions.json
│   ├── features.json
│   └── data_links.json
├── schemas/                # JSON schemas for validation
│   ├── products.schema.json
│   ├── services.schema.json
│   └── ...
├── resources/              # Original source files (PPL CSV, etc.)
│   └── ppl/               # Deutsche Post price list files
├── scripts/                # Python validation scripts
│   ├── validate_schemas.py
│   └── generate_metadata.py
├── .pre-commit-config.yaml # Pre-commit framework configuration
├── Makefile               # Build automation
├── pyproject.toml         # Python dependencies
├── mappings.json          # Schema-to-data mappings (source of truth)
└── metadata.json          # Generated checksums (auto-generated)
```

---

## 🎨 Code Quality Standards

### JSON Formatting

-   4-space indentation
-   Keys are kept in original order (not sorted)
-   Arrays are multi-line for readability
-   Uses Python's built-in `json.tool`

### Python Formatting

-   **Ruff** (formatting, linting, and auto-fixes - line length: 100)
-   **MyPy** (type checking)

---

## 🤝 Contributing

1. Fork the repository
2. Run `make setup` to install dependencies and hooks
3. Make your changes
4. Run `make quality` to validate
5. Commit (pre-commit hooks validate automatically)
6. If `metadata.json` was regenerated, stage it: `git add metadata.json` and commit again
7. Submit a pull request

### Adding New Data

1. Add your data to the appropriate JSON file
2. Ensure it follows the schema
3. Run `make validate` to check
4. Run `make format` to auto-format
5. Commit your changes
6. If `metadata.json` was regenerated, stage it: `git add metadata.json` and commit again

### Updating Schemas

1. Edit the schema file in `schema/`
2. Update corresponding data in `data/`
3. Run `make validate` to verify compatibility

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## ⚠️ Disclaimer

This is **reference data** for Deutsche Post/DHL services. Always verify current restrictions, pricing, and service availability with Deutsche Post before shipping.

Data accuracy is maintained on a best-effort basis. For official information, visit:

-   Deutsche Post: https://www.deutschepost.de
-   DHL: https://www.dhl.de

---

## 🔗 Related Resources

-   [Deutsche Post Official Website](https://www.deutschepost.de)
-   [DHL International Services](https://www.dhl.de)
-   [EU Sanctions Map](https://www.sanctionsmap.eu/)
-   [ISO 3166 Country Codes](https://www.iso.org/iso-3166-country-codes.html)

---

## Support

For questions, issues, or contributions:

-   📧 **E-Mail**: build@gruncellka.dev
-   📧 **Issues**: Open a GitHub issue
-   🔧 **Contributions**: Submit a pull request
-   📖 **Documentation**: Check this README and inline comments

---

🔳 gruncellka
