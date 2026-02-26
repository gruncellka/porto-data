# Porto Data

[![validation](https://github.com/gruncellka/porto-data/actions/workflows/validation.yml/badge.svg)](https://github.com/gruncellka/porto-data/actions/workflows/validation.yml)

**Structured JSON data for Deutsche Post shipping services**

A comprehensive, schema-validated dataset containing Deutsche Post pricing, restrictions, zones, features, services, and compliance frameworks for international postal services. All data is validated against JSON schemas and published as a self-contained package on **npm** and **PyPI**.

---

## Install

**npm** (scope: `@gruncellka`)

```bash
npm install @gruncellka/porto-data
```

**PyPI (Python)**

```bash
pip install gruncellka-porto-data
```

The package includes `data/`, `schemas/`, `mappings.json`, and `metadata.json` so you can validate and use the data offline. Data files reference canonical schema URLs (GitHub); schemas are shipped in the package for local validation.

---

## Use cases

- **E-commerce** — Calculate shipping costs and restrictions
- **Logistics** — Integrate Deutsche Post pricing and rules
- **Compliance** — Check shipping restrictions and sanctions
- **Research** — Analyze postal service patterns and policies
- **Educational** — Learn about international shipping regulations

---

## Data statistics

- **9 JSON files** with comprehensive postal data
- **9 JSON schemas** ensuring data integrity
- **100+ countries** covered in shipping zones
- **5 product types** (letters, merchandise)
- **3 active service types** (registered mail, insurance) — 2 services discontinued as of 2025-01-01
- **31 restrictions** with 19 compliance frameworks

---

## Data overview

| File                | Description                                                        |
| ------------------- | ------------------------------------------------------------------ |
| `products.json`     | Shipping products (letters, parcels, packages)                   |
| `services.json`     | Additional services (registered mail, insurance, etc.)             |
| `prices.json`       | Pricing by product, zone, and weight (with effective dates)        |
| `zones.json`        | Geographic zones and country mappings                             |
| `weight_tiers.json` | Weight brackets for pricing                                       |
| `dimensions.json`   | Size limits and specifications                                    |
| `features.json`     | Service features and capabilities                                 |
| `restrictions.json` | Shipping restrictions, sanctions, compliance frameworks           |
| `data_links.json`   | Cross-references between data files                                |

All data is validated against JSON schemas in `schemas/` (required fields, types, enums, ISO patterns, dates, cross-references). Schema-to-data mapping is in `mappings.json`; `metadata.json` provides checksums and canonical schema URLs.

---

## Data structure (high level)

- **Products → Prices → Zones** — Products reference dimensions and weight tiers; prices are per zone and weight with effective dates.
- **Services → Features** — Services reference features and apply to products.
- **Restrictions → Frameworks** — Restrictions reference compliance frameworks (e.g. EU sanctions, UN resolutions).

Relationships are one-directional (no circular dependencies). `data_links.json` describes dependencies, links, and lookup rules for SDKs and tooling.

---

## Standards

- **Country codes**: ISO 3166-1 alpha-2 (`DE`, `US`, `FR`, `YE`)
- **Region codes**: ISO 3166-2 (`DE-BY`, `US-CA`, `FR-75`)
- **Dates**: ISO 8601 (`2024-01-15`, `2023-06-01`)
- **Jurisdiction**: `EU` (European Union), `UN` (United Nations), `DE` (Germany), `DP` (Deutsche Post operational)

**Restrictions:** Tracks occupied/disputed territories, links to legal frameworks (EU sanctions, UN resolutions), supports partial territory restrictions (`effective_partial`) and historical dates (`effective_from`, `effective_to`).

---

## License

MIT — see [LICENSE](LICENSE).

---

## Disclaimer

This is **reference data** for Deutsche Post services. Always verify current restrictions, pricing, and service availability with Deutsche Post before shipping. Data accuracy is best-effort. Official information: [Deutsche Post](https://www.deutschepost.de).

---

## Related resources

- [Deutsche Post](https://www.deutschepost.de)
- [EU Sanctions Map](https://www.sanctionsmap.eu/)
- [ISO 3166 Country Codes](https://www.iso.org/iso-3166-country-codes.html)

---

## Contributing and development

Setup, validation, tests, and release details are in **[CONTRIBUTING.md](CONTRIBUTING.md)**. For full project structure and commands, see **[DEVELOPMENT.md](DEVELOPMENT.md)**.

- **Issues**: [GitHub Issues](https://github.com/gruncellka/porto-data/issues)
- **Contact**: build@gruncellka.dev
- **Contributions**: Pull requests welcome
- **Documentation**: CONTRIBUTING.md, DEVELOPMENT.md, and inline comments

---

gruncellka
