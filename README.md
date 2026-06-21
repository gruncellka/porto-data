# Porto Data

[![validation](https://github.com/gruncellka/porto-data/actions/workflows/validation.yml/badge.svg)](https://github.com/gruncellka/porto-data/actions/workflows/validation.yml)
[![codecov](https://codecov.io/gh/gruncellka/porto-data/branch/main/graph/badge.svg)](https://codecov.io/gh/gruncellka/porto-data)

**Porto Data** is **JSON + schemas** for national postal operators under one shared layout and vocabulary. Published on **npm** and **PyPI** with the **same** `porto_data/` tree on every platform.

The bundle covers **Deutsche Post**, **La Poste**, **Ukrposhta** and **Swiss Post** with shared policy/formats data at the bundle root and **per-operator** catalogs under **`providers/<id>/`** (products, services, prices, zones, weight tiers, features, limits, **`graph.json`**).

---

## Install

**TypeScript / JavaScript (npm)**

```bash
npm install @gruncellka/porto-data
```

**Python (PyPI)**

```bash
pip install gruncellka-porto-data
```

Shipped layout: **`porto_data/policy/`**, **`porto_data/formats/`**, **`porto_data/providers/<id>/`**, **`porto_data/schemas/`**, **`mappings.json`**, **`metadata.json`**. Resolve paths via **`mappings.json`** / **`metadata.json`** (no legacy flat `data/` tree).

- **Python:** `import porto_data` and open files relative to the package root.
- **TypeScript / JavaScript:** same paths (e.g. `porto_data/providers.json`, `porto_data/policy/restrictions.json`, `porto_data/providers/deutschepost/products.json`).

### Cross-platform (npm and PyPI)

Both packages ship **only UTF-8 JSON, schemas, `mappings.json`, and `metadata.json`**—**no native extensions**. The layout is identical on **Linux, macOS, and Windows**. PyPI includes a tiny Python helper (`import porto_data`); npm exposes `metadata.json` via `index.js`—the underlying files are normal JSON you can read from any language.

---

## Use cases

E-commerce and logistics (multi-carrier quotes, letters), compliance (sanctions, frameworks), research and education.

---

## Logical files (per operator unless noted)

| File                        | Description                                                                                                                                                                                                                                            |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `products.json`             | Letter (and related) products; **`unit.weight`** only (`g`); physical sizes via **`envelope_ids`** + global **`envelopes.json`** (`envelopes[]`: **`id`**, **`width`/`height`** mm)                                                                    |
| `services.json`             | Add-on services: **`porto_id`** (unified), provider **`id`**, native **`name`**, English **`label`**                                                                                                                                                   |
| `prices/products.json`      | Base letter postage grid (`file_type` **`product_prices`**): **`product_id`** × **`zone`** × **`weight_tier`** (effective-dated **`amount`** in cents)                                                                                                 |
| `prices/services.json`      | Add-on service amounts (`file_type` **`service_prices`**) keyed by **`service_id`** (matches catalog **`services.json`** **`id`**)                                                                                                                     |
| `zones.json`                | Geographic zones and country mappings                                                                                                                                                                                                                  |
| `weights.json`              | Weight brackets for pricing                                                                                                                                                                                                                            |
| `features.json`             | Operator-scoped **`id`**, unified **`porto_id`**, native **`name`**, English **`label`**                                                                                                                                                               |
| `limits.json`               | Operational limits and compliance framework metadata                                                                                                                                                                                                   |
| `graph.json`                | **`dependencies`** (file load order), **`edges`** (per product: allowed zones + weight tiers), **`services`**, **`unit`**                                                                                                   |
| `formats/layouts.json`        | Jurisdiction-keyed print/window geometry (**DE / CH / FR**) per envelope **`id`** (`file_type` **`layouts`**); optional **`standard`** (norm token, e.g. **DIN678**, **SN010130**, **NFEN13850**); physical sizes remain in **`formats/envelopes.json`** |
| `formats/envelopes.json`      | Physical envelope catalog: **`envelopes[]`** with **`id`**, **`width`/`height`**, **`standard`** `ISO269`, **`sheets[]`** (ISO 216 **`sheet`** + **`fold`**)                                                                                           |
| `policy/restrictions.json`  | Sanctions-style restrictions and compliance frameworks                                                                                                                                                                                                 |
| `policy/jurisdictions.json` | `jurisdictions.eu` / `jurisdictions.un` (ISO alpha-2; align with symbolic `EU` / `UN`)                                                                                                                                                                 |
| `policy/markets.json`       | Per-country currency, VAT, intl quote currencies (`markets[CC]`); resolved via `providers.json` `country`                                                                                                                                            |

All JSON validates against **`schemas/`**; **`mappings.json`** maps entities to paths; **`metadata.json`** has checksums and schema URLs.

**Cross-file rules:** **`graph.json` → `edges`** keys = **`products.json` `id`**. **`services`** and price rows reference native **`id`** (not **`porto_id`**) for **`product_id`** / **`service_id`**. **`porto_id`** is the **cross-operator** semantic id when native ids differ. **`services[].features`** may list feature **`id`** or **`porto_id`**.

**Tariff verification:** CI validates structure only — not that amounts match live carrier tables. See [docs/tariff-verification.md](docs/tariff-verification.md) and per-provider notes under [docs/providers/](docs/providers/).

**Provider tariff dating (catalog baseline):** In **`providers/<id>/products.json`**, **`prices/products.json`**, and **`prices/services.json`**, **`effective_from`** is the **bundle baseline** (**`2026-01-01`**) for the modeled **2026** tariff snapshot. Use **`effective_to`**: **`null`** until a row is superseded by a newer **`price[]`** entry. (Other files, e.g. **`policy/restrictions.json`** or **`limits.json`**, keep their own effective-dating semantics.)

---

## Standards

- **Country codes**: ISO 3166-1 alpha-2 (`DE`, `CH`, `FR`, …)
- **Region codes**: ISO 3166-2 (`DE-BY`, `CH-ZH`, `FR-75`)
- **Dates**: ISO 8601 (`2024-01-15`)
- **Jurisdiction** (global restrictions): `EU`, `UN`, national codes on sanction or law frameworks—not an operator id.

**`policy/restrictions.json`:** destination-oriented legal and sanctions regimes; framework metadata (`jurisdiction`, scope, optional IANA `timezone` for row `effective_*`). Row-level `effective_from` / `effective_to` drive activation.

**`providers/<id>/limits.json`:** that operator’s execution rules; framework **`timezone`** should match **`providers.json`** for the same id.

---

## Disclaimer

**Reference data only.** Confirm pricing, restrictions, and availability with the **carrier** you use before shipping. Not a substitute for official systems or legal advice.

---

## Related resources

- **Unified `porto_id` (cross-operator ids):** [docs/id.md](docs/id.md) · [docs/porto_id.md](docs/porto_id.md) · [docs/resolution.md](docs/resolution.md) · [docs/provider-template.md](docs/provider-template.md)
- **Tariff reconciliation (manual):** [docs/tariff-verification.md](docs/tariff-verification.md)

**Carriers in this bundle** — tariff / modeling notes, shipped JSON folder, and official site:

| Provider (`providers.json` id) | Reconciliation doc                                               | Bundle data folder                   | Website                                        |
| ------------------------------ | ---------------------------------------------------------------- | ------------------------------------ | ---------------------------------------------- |
| Deutsche Post (`deutschepost`) | [docs/providers/deutschepost.md](docs/providers/deutschepost.md) | `porto_data/providers/deutschepost/` | [deutschepost.de](https://www.deutschepost.de) |
| Swiss Post (`swisspost`)       | [docs/providers/swisspost.md](docs/providers/swisspost.md)       | `porto_data/providers/swisspost/`    | [post.ch](https://www.post.ch)                 |
| La Poste (`laposte`)           | [docs/providers/laposte.md](docs/providers/laposte.md)           | `porto_data/providers/laposte/`      | [laposte.fr](https://www.laposte.fr)           |
| Ukrposhta (`ukrposhta`)        | [docs/providers/ukrposhta.md](docs/providers/ukrposhta.md)       | `porto_data/providers/ukrposhta/`    | [ukrposhta.ua](https://ukrposhta.ua/)          |

**Other references:** [EU Sanctions Map](https://www.sanctionsmap.eu/), [ISO 3166 country codes](https://www.iso.org/iso-3166-country-codes.html)

---

🔳 gruncellka
