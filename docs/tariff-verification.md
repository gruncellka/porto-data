# Tariff verification

How we reconcile **product and service prices** in this bundle with official carrier sources. This is **reference data**, not a legal tariff publication.

**Provider notes:** [deutschepost.md](providers/deutschepost.md) · [ukrposhta.md](providers/ukrposhta.md) · [laposte.md](providers/laposte.md) · [swisspost.md](providers/swisspost.md)

---

## What CI checks vs what humans check

| Layer | Tool | Proves |
|-------|------|--------|
| Structure | `make validate` | Schema, graph edges, native ids, cross-file refs, porto_id enum |
| Amounts | Manual reconciliation (this doc + provider notes) | Cent/rappen amounts match official tables on a given date |

There is **no automated tariff oracle** in CI. Wrong amounts that still satisfy the schema will pass validation.

---

## Reconciliation workflow

1. Open the provider’s **Official sources** table (dated).
2. Copy anchor rows into **Official snapshots** (€ / CHF / UAH / USD as published).
3. Compare to **`prices/products.json`** and **`prices/services.json`** (amounts in **minor units**: cents / rappen).
4. Fix JSON or document intentional simplification under **Out of scope**.
5. Update **Verification status** (date + confidence).
6. Run `make validate` and `make metadata`.

---

## Multi-currency

File-level default: `unit.currency` in each price file. Row override: optional **`currency`** on a `product_prices` or `service_prices` row when that row is quoted in another currency ([`product_prices.schema.json`](../porto_data/schemas/product_prices.schema.json)).

**Market defaults:** `policy/markets.json` → `markets[providers.json country].currency`. Allowed intl row overrides: `markets[CC].intl_ccy` (array).

**Ukrposhta:** domestic rows in **UAH** (`markets.UA.currency`); international **letters** in **USD** (`intl_ccy: ["USD"]`); settlement in UAH at NBU rate on service date — see `markets.UA.settlement`.

---

## When a flat `world` zone is OK

Use one **`world`** zone (same amount for all destinations) when the carrier publishes a **single international letter table** without country columns:

- Deutsche Post — “Alle Länder – ein Preis – weltweit”
- Ukrposhta — **international letters** flat USD table at bottom of [taryfy](https://www.ukrposhta.ua/ua/taryfy)
- Swiss Post — flat international document ladder (EU = world in our minimal model)

Use **per-country or multi-zone** models when the official table is country- or zone-indexed:

- La Poste — international buckets from catalogue intégral
- Ukrposhta **parcels** — per-country matrix on the same site (not in this bundle yet)

---

## Verification status (bundle snapshot)

| Provider | Last checked (UTC) | Confidence | Notes |
|----------|-------------------|------------|-------|
| Deutsche Post | 2026-06-21 | verified | Letter ladder + Einschreiben surcharges vs deutschepost.de |
| Ukrposhta | 2026-06-21 | partial | Domestic + intl **letters** verified; parcels / personal intl / extra services deferred |
| La Poste | 2026-06-21 | verified | Lettre verte / suivie / Services Plus / recommandée vs laposte.fr 2026 tables |
| Swiss Post | 2026-06-21 | verified | A/B domestic + intl documents + thickness surcharge vs post.ch |

---

## Common pitfalls (all carriers)

- **VAT vs net:** some sites show VAT-inclusive (Ukrposhta domestic page) vs VAT-exempt (Deutsche Post letters). Match the column the carrier uses for the product you model.
- **Product vs surcharge:** registered / Einschreiben / AR are often **services** (`service_prices.json`), not separate products — unless the carrier sells them as standalone products (La Poste recommandée).
- **Weight tier ids:** JSON uses `W0020`, `W0050`, … — must match `graph.json` edges and official weight breaks.
- **Effective dating:** bundle baseline `effective_from: 2026-01-01` unless a row has a known later tariff start (e.g. Ukrposhta intl letters `2026-04-01`).

---

## Re-run after carrier price changes

When a carrier updates tariffs: edit provider JSON → update that provider’s MD snapshots and status date → `CHANGELOG.md` → `make metadata` → release.
