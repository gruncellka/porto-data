# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Breaking (bundle layout & resolution)

- **Layout:** Shared data is **`porto_data/policy/`** (restrictions, jurisdictions) and **`porto_data/mails/`** (envelopes, layouts). Per-operator data is **`porto_data/providers/<id>/`**. **`porto_data/providers.json`** is the provider registry at the bundle root (not under `global/`). Legacy flat **`porto_data/data/`** and **`data_links.json`** are removed; **`graph.json`** (`file_type` **`graph`**) holds **dependencies**, **`edges`** (product × zones × weight tiers), **lookup_rules**, and **global_settings**.
- **Prices:** **`providers/<id>/prices.json`** split into **`prices/products.json`** (`product_prices`) and **`prices/services.json`** (`service_prices`).
- **Weights:** **`weight_tiers.json`** → **`weights.json`** (schema **`weights.schema.json`**).
- **Products:** **`supported_zones`** → **`zones`**; physical formats via **`envelope_ids`** referencing **`mails/envelopes.json`**; **`unit`** is **`weight`** (`g`) only.
- **Features:** No global features file — only **`providers/<id>/features.json`**. **`services.json`** uses **`porto_id`**; graph/prices reference native service **`id`**.
- **Registry:** **`deutschepost`**, **`swisspost`**, **`laposte`**, **`ukrposhta`** in **`providers.json`** and **`mappings.json`**.

### Added

- **Docs:** Tariff alignment notes under **`docs/providers/`** (`deutschepost`, `laposte`, `swisspost`, `ukrposhta`). Unified **`porto_id`** docs: **`docs/id.md`**, **[`PORTO_ID_MAPPING.md`](PORTO_ID_MAPPING.md)**, **[`porto_id_normalization_plan.md`](porto_id_normalization_plan.md)** (cross-linked; see **`README.md`**).
- **Validation:** `porto validate` runs **schema → mappings → limits → graph** (`--type` is one of **`schema`**, **`mappings`**, **`limits`**, **`graph`**). Registry consistency is checked inside **mappings** validation.
- **Swiss Post:** Optional **`providers/swisspost/rules.json`** (e.g. thickness surcharge) where modeled.

### Changed (2026 tariff snapshot)

- Catalog baseline **`effective_from`: `2026-01-01`** on products and price rows where applicable.
- **Deutsche Post:** International letter pricing includes **`maxibrief_international_heavy`** (abroad); worldwide zone ladder per current tariff tables (see **`docs/providers/deutschepost.md`**).
- **Swiss Post:** No separate Midibrief in this catalog (standard vs large letter products); international **`zone_1_eu`** / **`world`** document-letter rows aligned with post.ch snapshot.
- **La Poste:** Letter lines include **`lettre_verte`**, suivie, services plus, recommandée tiers; services such as optional tracking and AR where modeled.

### Tooling

- **Python `>=3.13`** (see **[0.3.0]**). Graph validation in **`scripts/validators/graph.py`**; tests include **`tests/test_validate_graph.py`** (replaces data-links-era naming).

---

## [0.3.0] - 2026-03-06

### Changed

- **BREAKING:** Python baseline **3.13+** (`requires-python >=3.13`).
- **Tooling:** Ruff/MyPy aligned to Python **3.13**; pre-commit Ruff supports `py313`.
- **npm:** Node **>=20** (`engines.node`); TypeScript dev **~5.9.3**.

## [0.2.1] - 2026-03-01

### Added

- **npm:** `index.js` / `index.d.ts` entry and types.
- **PyPI:** `porto_data` exposes `metadata`, `__version__`, `get_package_root()`, `py.typed`.
- **`make test-publish`:** pack npm + wheel, install smoke test.

### Changed

- Publish workflow runs `tests/test_publish.sh` before release.

## [0.2.0] - 2026-02-28

### Changed

- Published npm/PyPI artifacts are **data + schemas only** (no CLI). **`bump2version`** tags **`v{version}`** for releases.

## [0.1.0] - 2025-12-21

### Added

- **`porto`** CLI: **`validate`** (schema, mappings, limits, graph), **`metadata`**; modular **`scripts/validators/`** and **`scripts/data_files.py`**.

### Changed

- **BREAKING:** Imports use **`scripts.*`** / **`cli.*`** package paths (no `sys.path` hacks).
- Graph validation lives in **`scripts/validators/graph.py`** (**`edges`** in **`graph.json`**).

## [0.0.1] - 2025-10-22

### Added

- Initial Deutsche Post–focused bundle, JSON schemas, CI, pre-commit, **`porto_data`** layout with **`graph.json`**.
