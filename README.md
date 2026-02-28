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

- **PyPI**: After `pip install`, use the `porto` CLI or import the `porto_data` package; paths are resolved automatically.
- **npm**: Data lives under `porto_data/` (e.g. `porto_data/data/products.json`, `porto_data/schemas/`, `porto_data/mappings.json`, `porto_data/metadata.json`). Same layout in both ecosystems; the `porto_data` folder exists so the wheel includes the files correctly.

---

## Use cases

E-commerce and logistics (shipping costs, restrictions), compliance (sanctions, frameworks), research and education.

---

## Data statistics

9 JSON files, 9 schemas; 190+ countries in zones; 5 product types; 5 service types (e.g. registered mail); 31 restrictions across 18 compliance frameworks.

---

## Data overview and structure

| File                | Description                                                 |
| ------------------- | ----------------------------------------------------------- |
| `products.json`     | Shipping products (letters, parcels, packages)              |
| `services.json`     | Additional services (registered mail, etc.)                 |
| `prices.json`       | Pricing by product, zone, and weight (effective dates)      |
| `zones.json`        | Geographic zones and country mappings                       |
| `weight_tiers.json` | Weight brackets for pricing                                 |
| `dimensions.json`   | Size limits and specifications                              |
| `features.json`     | Service features and capabilities                           |
| `restrictions.json` | Shipping restrictions, sanctions, compliance frameworks      |
| `data_links.json`   | Cross-references between data files                         |

All data is validated against JSON schemas in `schemas/`; `mappings.json` maps schemas to files; `metadata.json` has checksums and canonical URLs. **Structure:** Products → Prices → Zones (dimensions, weight tiers, effective dates); Services → Features; Restrictions → Frameworks (e.g. EU sanctions, UN resolutions). One-directional; no circular dependencies. `data_links.json` describes dependencies and lookup rules.

---

## Standards

- **Country codes**: ISO 3166-1 alpha-2 (`DE`, `US`, `FR`, `YE`)
- **Region codes**: ISO 3166-2 (`DE-BY`, `US-CA`, `FR-75`)
- **Dates**: ISO 8601 (`2024-01-15`, `2023-06-01`)
- **Jurisdiction**: `EU` (European Union), `UN` (United Nations), `DE` (Germany), `DP` (Deutsche Post operational)

**Restrictions:** Tracks occupied/disputed territories, links to legal frameworks (EU sanctions, UN resolutions), supports partial territory restrictions (`effective_partial`) and historical dates (`effective_from`, `effective_to`).

---

## Disclaimer

This is **reference data** for Deutsche Post services. Always verify current restrictions, pricing, and service availability with Deutsche Post before shipping. Data accuracy is best-effort. Official information: [Deutsche Post](https://www.deutschepost.de).

---

## Related resources

- [Deutsche Post](https://www.deutschepost.de)
- [EU Sanctions Map](https://www.sanctionsmap.eu/)
- [ISO 3166 Country Codes](https://www.iso.org/iso-3166-country-codes.html)

---

🔳 gruncellka
