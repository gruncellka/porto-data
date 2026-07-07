# Deutsche Post — `porto_data/providers/deutschepost/`

Reference for **reconciling JSON with official letter/postcard tariffs** (not a legal tariff publication). Verify on [deutschepost.de](https://www.deutschepost.de) and current **Preisblätter** before production changes.

**Related:** [mark-profiles.md](../mark-profiles.md) · [ukrposhta.md](ukrposhta.md) · [laposte.md](laposte.md) · [swisspost.md](swisspost.md) · [tariff-verification.md](../tariff-verification.md)

---

## Verification status

| Field | Value |
|-------|--------|
| Last checked (UTC) | 2026-06-21 |
| Confidence | **verified** — domestic + international letter ladder + Einschreiben surcharges |
| Tariff period | Prices fixed **2025-01-01** through **2026-12-31** (Bundesnetzagentur); JSON `effective_from`: **2026-01-01** |

---

## Files in this provider (and shared deps)

| Path | `file_type` | Role |
|------|-------------|------|
| `products.json` | `products` | Product ids, zones, weights, envelope refs, services |
| `prices/products.json` | `product_prices` | Base postage grid (product × zone × weight tier) |
| `prices/services.json` | `service_prices` | Surcharges (Einschreiben, etc.) |
| `services.json` | `services` | Service definitions |
| `features.json` | `features` | Feature ids used by services |
| `marks.json` | `marks` | Mark/label profiles and optional checkout calibrations |
| `integrations.json` | `integrations` | SDK execution manifest (`internetmarke`, capabilities) |
| `weights.json` | `weights` | Weight tier ids (`W0020` …) |
| `zones.json` | `zones` | Domestic / EU / Europe / world buckets |
| `limits.json` | `limits` | Provider operational overlays on top of global policy (often empty) |
| `graph.json` | `graph` | Edges, units (EUR cents), `services` |

**Loaded with the bundle:** `policy/jurisdictions.json`, `policy/markets.json`, `policy/restrictions.json`, `formats/envelopes.json`, `formats/layouts.json` — see `graph.json` `dependencies`.

---

## Known pitfalls

- **International single price:** consumer pages use **“Alle Länder – ein Preis – weltweit”** — `zone_1_eu`, `zone_2_europe`, and `world` must share the **same** cent amounts per product/tier (do not invent regional splits).
- **Add-ons vs products:** Einschreiben variants are **surcharges** in `prices/services.json`, not separate products.
- **VAT-free letters:** Deutsche Post letter prices are **umsatzsteuerfrei** on official pages — amounts map 1:1 to euro cents.
- **Maxibrief Plus (5,10 € domestic):** separate format — **not** in `products.json`.

---

## Pricing & geography rules (how we model)

- **Domestic:** prices by **format + weight** (no domestic “zone”).
- **International:** flat worldwide ladder per format/weight (see pitfalls).
- **Add-ons:** Einschreiben etc. in `prices/services.json`.

## Service support (proof/signature/AR)

- **Proof of mailing:** Internetmarke + Einschreiben → **Einlieferungsbeleg** once scanned.
- **Recipient signature:** `einschreiben` requires signature; `einschreiben_einwurf` does not (mailbox + tracking).
- **Return receipt:** `einschreiben_rueckschein` in `service_prices.json`.

---

## Official sources (checklist)

| Date (UTC) | Source | Use |
|------------|--------|-----|
| 2026-06-21 | [Briefe in Deutschland](https://www.deutschepost.de/de/b/briefe-in-deutschland.html) | Domestic ladder 2026 |
| 2026-06-21 | [Brief International](https://www.deutschepost.de/de/b/briefe-ins-ausland/brief-postkarte-international.html) | Worldwide single-price ladder |
| 2026-06-21 | [Internetmarke](https://www.deutschepost.de/de/i/internetmarke-porto-drucken.html) | Product scope |
| — | PDF Gesamtpreisliste (`dp-leistungen-und-preise-*.pdf` on site) | Authoritative PDF, effective dates |

---

## Official snapshots (€ — from deutschepost.de, 2026)

**Domestic:** Standard / Postkarte **0,95** · Kompakt **1,10** · Groß **1,80** · Maxi **2,90**.

**International (worldwide):** Standard / Postkarte **1,25** · Kompakt **1,80** · Groß **3,30** · Maxi **6,50** · heavy Maxi (1,001–2,000 g) **17,00**.

**Einschreiben (add to base):** Einwurf **+2,35** · standard **+2,65** · Rückschein **+4,85**.

---

## In-repo alignment (`effective_from`: `2026-01-01`, amounts in **cents**)

| `product_id` | Domestic | International (`zone_1_eu`, `zone_2_europe`, `world`) | Notes |
|--------------|---------:|--------------------------------------------------------:|-------|
| `standardbrief` | 95 | 125 | W0020 |
| `kompaktbrief` | 110 | 180 | W0050 |
| `grossbrief` | 180 | 330 | W0500 |
| `maxibrief` | 290 | 650 | W1000 |
| `maxibrief_international_heavy` | — | 1700 | Abroad only, W2000 |

**`service_prices` (cents):** `einschreiben` 265 · `einschreiben_einwurf` 235 · `einschreiben_rueckschein` 485 · `zusatzversicherung` 250.

**Graph:** weight tiers in official ladder must appear in **`edges`**; prices via `dependencies` + `prices/products.json` / `prices/services.json`.

---

## Mark profiles & Internetmarke calibrations

Cross-provider resolution rules: [mark-profiles.md](../mark-profiles.md).

### Zone × service → profile

| Zone | Selected services | Profile id |
|------|-------------------|------------|
| `domestic` | none | `domestic` |
| `world` | none | `international` |
| `domestic` | `einschreiben` | `registered` |
| `world` | `einschreiben` | `registered_international` |

Mapped in `graph.json` → `edges.marks`; catalog sizes in `marks.json` → `profiles[]`.

### Internetmarke checkout calibrations

`marks.json` → `calibrations[]` at checkout **DPI300** (measured from live Internetmarke output):

| `voucher_layout` | Asset | Size (mm) | Size (px) |
|------------------|-------|-----------|-----------|
| `FRANKING_ZONE` | Marke only (per `mark_profile`) | 37×20 · 62×20 · 62×32.5 | 437×236 · 732×236 · 732×384 |
| `ADDRESS_ZONE` | Full label (all profiles) | **85×43** | **1004×508** |

`profiles[].size` is nominal marke footprint (mm). Per-layout px/mm at a given checkout dpi is in `calibrations[]` (`by_mark_profile` or `label_canvas`).

---

## Out of scope

- `postkarte` as separate product (same € as Standardbrief — not in `products.json`)
- **Maxibrief Plus** (5,10 €, 2 kg domestic)
- **Warensendung** and other non-letter Internetmarke products

---

## Reconcile

Latest Preisblätter / deutschepost.de → diff `prices/*.json`, `graph.json` → update this doc’s status date → `make validate` → `make metadata`.
