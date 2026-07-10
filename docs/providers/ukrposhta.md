# Ukrposhta — `porto_data/providers/ukrposhta/`

Reference for **reconciling JSON with official letter tariffs** (not a legal tariff publication). Verify on [ukrposhta.ua](https://www.ukrposhta.ua) and current PDF tariffs before production changes.

---

## Bundle scope (letters only)

This catalog models **letters only** — no parcels, postcards, personal-delivery letter columns, inventory-description variants, or EMS/SMALL_BAG flows.

| Layer | In bundle |
|-------|-----------|
| Products | `lyst_standartnyi` (`porto_id` **`small`**) — domestic + international; `dokument` (`porto_id` **`large`**) — domestic flat document letter only |
| Services | Return receipt (paper/electronic); international registered surcharge |
| Zones | `domestic`, flat `world` (international letters) |

**`porto_id`:** SDK input uses `small` or `large` only for Ukrposhta products. `large` is **only** `dokument` (domestic); international letter postage is always `small` on `lyst_standartnyi`. See [resolution.md](../resolution.md) § Ukrposhta.

---

## Verification status

| Field | Value |
|-------|--------|
| Last checked (UTC) | 2026-06-21 |
| Confidence | **verified** — domestic + international **letters** (in-scope products and services above) |
| Baseline | `effective_from` **2026-01-01** (domestic); international letter rows **2026-04-01** |

---

## Files in this provider (and shared deps)

| Path | `file_type` | Role |
|------|-------------|------|
| `products.json` | `products` | `lyst_standartnyi`, `dokument` |
| `prices/products.json` | `product_prices` | Domestic UAH + international USD letter grid |
| `prices/services.json` | `service_prices` | AR + international registered surcharge |
| `services.json` | `services` | Service definitions |
| `features.json` | `features` | Features for services |
| `marks.json` | `marks` | Label profiles |
| `weights.json` | `weights` | Weight tiers |
| `zones.json` | `zones` | `domestic`, flat `world` (letters) |
| `limits.json` | `limits` | Provider overlays |
| `graph.json` | `graph` | Edges, units (default UAH cents), `services` |

**Loaded with the bundle:** `policy/jurisdictions.json`, `policy/markets.json`, `policy/restrictions.json`, `formats/envelopes.json`, `formats/layouts.json` — see `graph.json` `dependencies`.

---

## Known pitfalls

- **Two currencies:** domestic **UAH** (`markets.UA.currency`, VAT inclusive); international **letters** quoted in **USD** (`markets.UA.international_currency`) without VAT on tariff table — paid in **UAH** at [NBU rate](https://www.ukrposhta.ua/en/faq-oplata-posluhi) on service date (`markets.UA.settlement`). Use row-level `currency: "USD"` for international rows; do not convert to UAH in JSON.
- **Letters vs parcels:** [taryfy](https://www.ukrposhta.ua/ua/taryfy) **parcel** tables are **per-country** (USD). **Letter** table is a **flat** ladder (easy to miss — bottom of page). Do not use parcel matrices for letter products.
- **VAT footnotes:** domestic site shows **грн з ПДВ**; international letter table **без ПДВ**. Registered international has separate VAT rules on domestic portion (80 UAH portion cited on site for e-label flows).
- **Personal delivery (international):** official letter table has a second column (“з особистим врученням”) — **out of scope** (letters-only bundle; e.g. ≤50 g **6 USD** vs **2.5 USD** standard).
- **Priority vs non-priority:** merged to single priority tariff from 2026 — no split in data.

---

## Pricing & geography rules (how we model)

- **Domestic:** `lyst_standartnyi` (`porto_id` **`small`**) — ≤50 g and 50 g–2 kg steps; `dokument` (`porto_id` **`large`**) — flat domestic document letter to 1 kg (Ukrposhta “Документ”; not a parcel SKU).
- **International letters:** single product `lyst_standartnyi` + zone **`world`** + USD amounts; flat table applies to all destinations in `zones.json` `world.country_codes`.
- **Services:** AR paper/electronic and international registered are **surcharges** in `prices/services.json`.

---

## Official sources (checklist)

| Date (UTC) | Source | Use |
|------------|--------|-----|
| 2026-06-21 | [Тарифи листи та документи](https://www.ukrposhta.ua/uk/taryfy-ukrposhta-dokumenty) | Domestic letters, AR, Dokument (UAH with VAT) |
| 2026-06-21 | [Тарифи / taryfy](https://www.ukrposhta.ua/ua/taryfy) → **Міжнародні листи та листівки, USD** | Flat international letter ladder |
| 2026-06-21 | [Тарифи споживача 2026 (PDF)](https://www.ukrposhta.ua/doc/kutochok-spozhyvacha/taryfy_ukrposhty_na_2026_rik.pdf) | Consumer corner — cross-check domestic |
| 2026-06-21 | [Міжнародні тарифи 01.01.2026 (PDF)](https://www.ukrposhta.ua/doc/tariffs/taryfy_mzhd_01012026.pdf) | Registered surcharge **3,50 USD** (letters); parcel tables ignored |
| — | [dev.ukrposhta.ua documentation](https://dev.ukrposhta.ua/documentation) | API `LETTER` only for this bundle (`PARCEL` out of scope) |

---

## Official snapshots

**Domestic letters (UAH, with VAT — site)**

| Product | ≤50 g | 50 g–2 kg |
|---------|------:|----------:|
| Standard letter | 24 | 72 |
| Ukrposhta Dokument (≤1 kg) | — | 55 (flat) |

**Return receipt (UAH, with VAT)**

| Service | Amount |
|---------|-------:|
| Paper | 48 |
| Electronic | 24 |

**International letters (USD, without VAT — flat table on taryfy)**

| Weight | Standard letter |
|--------|----------------:|
| ≤50 g | 2.50 |
| ≤250 g | 4.00 |
| ≤1000 g | 14.50 |
| ≤2000 g | 28.50 |

**International registered (USD, without VAT — PDF art. 3–4)**

| Service | Surcharge |
|---------|----------:|
| Per registered item (letters) | **3.50** (in addition to weight tariff) |

---

## In-repo alignment

**`product_prices`** (`unit.currency`: **UAH**; international rows override **USD**)

| `product_id` | Zone | Tier | Amount | Currency | Notes |
|--------------|------|------|-------:|----------|-------|
| `lyst_standartnyi` | `domestic` | W0050 | 2400 | UAH | ≤50 g |
| `lyst_standartnyi` | `domestic` | W0250, W1000, W2000 | 7200 | UAH | 50 g–2 kg |
| `dokument` | `domestic` | W1000 | 5500 | UAH | Dokument flat |
| `lyst_standartnyi` | `world` | W0050 | 250 | USD | ≤50 g |
| `lyst_standartnyi` | `world` | W0250 | 400 | USD | ≤250 g |
| `lyst_standartnyi` | `world` | W1000 | 1450 | USD | ≤1000 g |
| `lyst_standartnyi` | `world` | W2000 | 2850 | USD | ≤2000 g |

**`service_prices`**

| `service_id` | Amount | Currency |
|--------------|-------:|----------|
| `paperove_povidomlennia_vruchennia` | 4800 | UAH |
| `elektronne_povidomlennia_vruchennia` | 2400 | UAH |
| `mizhnarodne_zareiestrovane` | 350 | USD |

**Graph:** `graph.json` `unit.currency` = **UAH** (default); international price rows carry **`currency: "USD"`**.

---

## Out of scope (letters-only bundle)

- Postcards (`листівки`) as separate product
- Domestic **personal delivery** / declared-value letter variants (48 / 96 UAH)
- International **personal delivery** letter column (6 / 7.5 / 18 / 32 USD)
- **Inventory description** online / branch (24 / 48 UAH)
- **Parcels**, SMALL_BAG, EMS — per-country USD matrices on [taryfy](https://www.ukrposhta.ua/ua/taryfy)
- Ground vs avia split, zone_1/2/3 from API appendix (in-scope letters use flat `world` instead)
- FX conversion to UAH at quote time (consumer/settlement concern)

---

## Reconcile

1. Domestic: [taryfy-ukrposhta-dokumenty](https://www.ukrposhta.ua/uk/taryfy-ukrposhta-dokumenty) → `prices/products.json` + `prices/services.json` (UAH).
2. Intl letters: [taryfy](https://www.ukrposhta.ua/ua/taryfy) letter table → `world` rows (USD).
3. Registered international: PDF / taryfy footnotes → `mizhnarodne_zareiestrovane`.
4. `make validate` → `make metadata`.
