# Porto Data

[![validation](https://github.com/gruncellka/porto-data/actions/workflows/validation.yml/badge.svg)](https://github.com/gruncellka/porto-data/actions/workflows/validation.yml)
[![codecov](https://codecov.io/gh/gruncellka/porto-data/branch/main/graph/badge.svg)](https://codecov.io/gh/gruncellka/porto-data)

**Porto Data** is **JSON + schemas** for national postal operators under one shared layout and vocabulary. Published on **npm** and **PyPI** with the **same** `porto_data/` tree on every platform.

The bundle covers **Deutsche Post**, **Ukrposhta**, **La Poste**, and **Swiss Post** (Die Post) with shared policy/formats data at the bundle root and **per-operator** catalogs under **`providers/<id>/`** (products, services, prices, zones, weight tiers, features, limits, **`graph.json`**). Registry display names: **`providers.json`** → **`label`**; legal entities: **`name`**.

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
| `limits.json`               | Provider operational overlay on global policy (**`limits[]` often empty**; see [docs/policy.md](docs/policy.md)) |
| `graph.json`                | **`dependencies`** (file load order), **`edges`** (per product: allowed zones + weight tiers), **`services`**, **`unit`**                                                                                                   |
| `marks.json`                | Franking footprint catalog: **`profiles[]`** (size, `mark_type`), **`zones`** (zone → lane profile id)                                                                                                              |
| `formats/layouts.json`        | Jurisdiction-keyed print/window geometry (**DE / CH / FR**) per envelope **`id`** (`file_type` **`layouts`**); optional **`standard`** (norm token, e.g. **DIN678**, **SN010130**, **NFEN13850**); physical sizes remain in **`formats/envelopes.json`** |
| `formats/envelopes.json`      | Physical envelope catalog: **`envelopes[]`** with **`id`**, **`width`/`height`**, **`standard`** `ISO269`, **`sheets[]`** (ISO 216 **`sheet`** + **`fold`**)                                                                                           |
| `policy/restrictions.json`  | Sanctions-style restrictions and compliance frameworks                                                                                                                                                                                                 |
| `policy/jurisdictions.json` | `jurisdictions.eu` / `jurisdictions.un` (ISO alpha-2; align with symbolic `EU` / `UN`)                                                                                                                                                                 |
| `policy/markets.json`       | Per-country **`currency`**, **`vat`**, **`international_currency`**, optional **`settlement`** — via `providers.json` `country` → [docs/policy.md](docs/policy.md) · [docs/resolution.md](docs/resolution.md) |

All JSON validates against **`schemas/`**; **`mappings.json`** maps entities to paths; **`metadata.json`** has checksums and schema URLs.

**Cross-file rules:** native **`id`** in graph/prices; **`porto_id`** for cross-operator input — see [docs/resolution.md](docs/resolution.md).

**Tariff verification:** CI validates structure only — not that amounts match live carrier tables. See [docs/tariff-verification.md](docs/tariff-verification.md) and per-provider notes under [docs/providers/](docs/providers/).

**Provider tariff dating (catalog baseline):** In **`providers/<id>/products.json`**, **`prices/products.json`**, and **`prices/services.json`**, **`effective_from`** is the **bundle baseline** (**`2026-01-01`**) for the modeled **2026** tariff snapshot. Use **`effective_to`**: **`null`** until a row is superseded by a newer **`price[]`** entry. (Other files, e.g. **`policy/restrictions.json`** or **`limits.json`**, keep their own effective-dating semantics.)

---

## Standards

- **Country / region / dates:** ISO 3166-1 alpha-2, ISO 3166-2, ISO 8601.
- **Policy vs operator overlays:** [docs/policy.md](docs/policy.md) (`restrictions`, `markets`, `jurisdictions` vs `limits.json`).
- **Currency / VAT resolution:** [docs/resolution.md](docs/resolution.md) § Currency and VAT.

---

## Disclaimer

**Reference data only.** Confirm pricing, restrictions, and availability with the **carrier** you use before shipping. Not a substitute for official systems or legal advice.

---

## Related resources

- **Mark profiles:** [docs/mark-profiles.md](docs/mark-profiles.md) — sizes and `zones`.
- **Policy & fiscal defaults:** [docs/policy.md](docs/policy.md)
- **Unified `porto_id`:** [docs/id.md](docs/id.md) · [docs/porto_id.md](docs/porto_id.md) · [docs/resolution.md](docs/resolution.md) · [docs/provider-template.md](docs/provider-template.md)
- **Tariff reconciliation:** [docs/tariff-verification.md](docs/tariff-verification.md)

**Carriers in this bundle** — tariff / modeling notes, shipped JSON folder, and official site:

| Provider (`providers.json` id) | Label | Legal name (`name`) | Reconciliation doc                                               | Bundle data folder                   | Website                                        |
| ------------------------------ | ----- | ------------------- | ---------------------------------------------------------------- | ------------------------------------ | ---------------------------------------------- |
| `deutschepost` | Deutsche Post | Deutsche Post AG | [docs/providers/deutschepost.md](docs/providers/deutschepost.md) | `porto_data/providers/deutschepost/` | [deutschepost.de](https://www.deutschepost.de) |
| `ukrposhta` | Ukrposhta | Ukrposhta JSC | [docs/providers/ukrposhta.md](docs/providers/ukrposhta.md)       | `porto_data/providers/ukrposhta/`    | [ukrposhta.ua](https://ukrposhta.ua/)          |
| `laposte` | La Poste | La Poste S.A. | [docs/providers/laposte.md](docs/providers/laposte.md)           | `porto_data/providers/laposte/`      | [laposte.fr](https://www.laposte.fr)           |
| `swisspost` | Swiss Post | Die Schweizerische Post AG | [docs/providers/swisspost.md](docs/providers/swisspost.md)       | `porto_data/providers/swisspost/`    | [post.ch](https://www.post.ch)                 |

**Other references:** [EU Sanctions Map](https://www.sanctionsmap.eu/), [ISO 3166 country codes](https://www.iso.org/iso-3166-country-codes.html)

---

🔳 gruncellka
