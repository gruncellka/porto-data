# Ukrposhta — `porto_data/providers/ukrposhta/`

Working notes for modeling **letters** (domestic + international) in porto-data and wiring them into the existing resolution graph / rules + SDK resolver stack.

---

## Sources (current)
- **Tariffs (domestic letters/documents)**: [ukrposhta.ua/uk/taryfy-ukrposhta-dokumenty](https://www.ukrposhta.ua/uk/taryfy-ukrposhta-dokumenty) — letters ≤50 g **24 UAH**, 50 g–2 kg **72 UAH**, personal delivery **48/96 UAH**, “Ukrposhta Dokument” **55 UAH** (includes 500 UAH declared value + A4 envelope), AR paper **48 UAH**, AR electronic **24 UAH**, inventory description online **30 UAH** / at branch **50 UAH**.
- **International API doc (ENG, 2025-06-24)**: `international_documentation_24062025_ENG.pdf` from https://dev.ukrposhta.ua/documentation → describes package types **LETTER / SMALL_BAG / PARCEL**, tariff endpoint `/dictionaries/tariffs/international/wrapper` (priceGround / priceAvia in **USD**, recommended surcharge, declared value surcharge %), and **size limits**: any side ≤ **60 cm**, sum of sides ≤ **90 cm**; rolls: length + 2×diameter ≤ **104 cm**, max dimension 90 cm. LETTER cannot carry declared value.
- **Tariff zones (international)**: Appendix C (same PDF) splits destinations into **3 zones**. Zone 1 ≈ CIS + Europe + Middle East/N. Africa; Zone 2 = East Asia + North America; Zone 3 = rest of Asia/Americas/Africa/Oceania. Need full country code list from appendix when building `zones.json`.
- **Label formats**: Same PDF lists printable sizes — LETTER supports **SIZE_A5 (default), SIZE_A6, SIZE_A4, SIZE_10X10**.
- **Swagger/OAS**: `https://www.ukrposhta.ua/ecom/0.0.1/api-docs` (referenced in Appendix B).

---

## Product surface we need to model
Domestic
- `letter_standard` (porto_id `letter_eco`): ≤50 g 24 UAH, 50 g–2 kg 72 UAH. Mark type: **label** (API returns PDF DL). Tracking: unclear for basic letter; assume **none** unless AR/personal-delivery chosen.
- `letter_personal_delivery` (porto_id `letter_signed`?): doubles the base price (48/96 UAH); recipient signature implied.
- `letter_return_receipt_paper` / `letter_return_receipt_elec` as services (AR) applicable to the above.
- `letter_inventory_desc_online` / `_branch` as services (inventory description surcharge).
- `letter_document` (porto_id `documents`): 55 UAH flat, includes declared value 500 UAH and special A4 envelope. Likely tracked; mark type label.

International (LETTER focus; SMALL_BAG similar grid if/when needed)
- Package type **LETTER** only (no declared value allowed).
- Transport modes: **priceGround** vs **priceAvia** per weight + zone. We should model as **two products** (`letter_int_ground`, `letter_int_avia`) to keep PriceResolver deterministic; transport mode is part of product, not a surcharge.
- Weight steps from `/dictionaries/tariffs/international/wrapper`: 0–250 g, 250–500 g, 500–1000 g, 1000–2000 g (values in USD; sample zone 1: 1.5 / 2.5 / 5 / 9 / 14 / 15 shown).
- Service surcharges in response: `recommendedSurcharge` (registered), `declaredStatusSurcharge`, `declaredPriceSurcharge` (%) — but **LETTER forbids declared value**, so only `recommended` is relevant.
- Label size options per request (A5/A6/A4/10×10).

Dimensions & limits
- UI shows “Максимальна сторона 40 см” for letters; international API enforces **≤60 cm and sum ≤90 cm**. Need to confirm domestic cap (40 cm vs 60 cm) and pick stricter for `limits.json` / `rules.json`.
- Rolls limit (if ever exposed) from API: length + 2×diameter ≤104 cm, max dimension 90 cm.

---

## Data-model plan (`porto_data/providers/ukrposhta/`)
- **Units** in `graph.json`: weight `g`, dimension `mm`, price `cents`, currency **UAH** (domestic). For international tariffs in **USD**, decide whether to store as **USD cents** (graph.currency = USD) or convert to UAH at a fixed rate (risk: FX drift). Recommend **keep USD** for now and mark currency accordingly.
- **Files to add** (same dependency pattern as La Poste / Swiss Post):
  - `products.json`, `weights.json`, `zones.json`, `services.json`, `features.json`, `marks.json`, `limits.json`, `prices/products.json`, `prices/services.json`, `graph.json`, optional `rules.json`.
- **Weight tiers**:
  - Domestic: `W0050` (0–50 g), `W2000` (50–2000 g) or split into `W0100`/`W0500` if future granularity appears.
  - International LETTER: `W0250`, `W0500`, `W1000`, `W2000` (match tariff rows).
- **Zones**:
  - `domestic` → `["UA"]`.
  - `zone_1`, `zone_2`, `zone_3` from Appendix C country lists (explicit ISO codes).
- **Products** (draft):
  - `letter_standard` (porto_id `letter_eco`, zones: domestic, mark_type `label`, tracking_mode `none`).
  - `letter_personal_delivery` (porto_id `letter_signed`, zones: domestic, mark_type `label`, tracking_mode `included`).
  - `letter_document` (porto_id `documents`, zones: domestic, mark_type `label`, tracking_mode `included`, declared_value_included = 500 UAH in description).
  - `letter_int_ground` / `letter_int_avia` (porto_id `letter_international`, zones: zone_1/2/3, mark_type `label`, tracking_mode likely `included` when `recommended` is chosen; base could be `optional`).
- **Services**:
  - `personal_delivery` (if modeled as service rather than separate product) — but tariff doubles base price, so product variant is simpler.
  - `return_receipt_paper`, `return_receipt_electronic` (map to AR prices).
  - `inventory_description_online`, `inventory_description_branch`.
  - `recommended` (registered surcharge for international).
  - `declared_value` should **not** be applicable to LETTER; either omit or forbid via rules.
- **Prices**:
  - `prices/products.json`: domestic ladder (24 / 72 UAH) and document 55 UAH; international grid per zone × weight × (ground/avia) in **USD cents**.
  - `prices/services.json`: AR amounts, inventory description surcharges, recommended surcharge (international).
- **Graph edges**:
  - Domestic products: zones `[domestic]`, weight_tiers per above.
  - International: each of `letter_int_ground`/`letter_int_avia` has zones `[zone_1, zone_2, zone_3]` and tiers `[W0250, W0500, W1000, W2000]`.
- **rules.json** (provider_rules):
  - Dimension guard: `kind: metric_band_reject` (or similar) enforcing side ≤ 600 mm and sum ≤ 900 mm; tune to 400 mm if domestic cap confirmed.
  - Service prohibition: reject `declared_value` for `packageType=LETTER` (model as `product_ids: [letter_*]` + `disallowed_services: [declared_value]` once schema permits; otherwise exclude service from products).
  - Optional: auto-attach `recommended` surcharge if barcode/registered flag set in adapter payload.

---

## Resolver / SDK fit
- **Data loader is provider-parameterized** (`ValidatedPortoDataLoader` / `PortoDataLoader` take `provider`), so adding `providers/ukrposhta/*` + `graph.json` is sufficient for resolution; no resolver code change expected.
- **Price resolution**: use standard lookup `product_prices (product_id + zone + weight_tier)` + `service_prices`. Transport mode split into distinct product_ids keeps lookup deterministic.
- **Mark semantics**: all Ukrposhta letter flows produce **labels/PDFs**, not stamps. Set `mark_type=label`, `tracking_mode` per product/service (e.g., `recommended` implies tracking).
- **Restrictions**: global `policy/restrictions.json` already loaded; Ukrposhta-specific size rules live in `limits.json` + `rules.json` for post-load checks.
- **Adapter implications**:
  - Auth: Bearer token + user token (per dev.ukrposhta.ua docs).
  - Endpoints: create shipment `/shipments?token=...`, fetch tariffs `/dictionaries/tariffs/international/wrapper`, print labels/forms (`/international/shipments/{id}/forms?size=SIZE_A5|A6|A4|10X10`), tracking numbers returned as barcodes (e.g., `RA...UA`).
  - Map provider response → `PortoMark` (`content` PDF, `tracking_number`, `external_id`, `format` size).

## Service support (proof/signature/AR)
- **Proof of mailing:** domestic registered (рекомендований лист) yields a posting receipt at the counter; online flow should surface acceptance id/tracking.
- **Recipient signature:** `personal_delivery` and registered flows require signature on delivery.
- **Return receipt:** AR available as **paper** or **electronic** add-on domestically; international registered (recommended) exposes a registered flow but no declared value for LETTER.

---

## Open items / decisions
- Confirm **domestic size cap** (UI shows 40 cm; API doc says 60 cm/90 cm sum). Model the stricter value unless official domestic PDF contradicts.
- Decide **currency** for international tariffs in porto-data (keep USD vs convert to UAH).
- Confirm which domestic letter products include tracking by default; if none, set `tracking_mode=none` and rely on `recommended/AR` services to add tracking.
- Fetch the latest **domestic API PDF** (API_documentation_09032026_eng.pdf) when accessible to validate weight tiers and service names before finalizing JSON.

---

## Next steps (data)
- Create `providers/ukrposhta/` folder with baseline schema files and `graph.json` mirroring dependency layout from La Poste / Swiss Post.
- Encode zones from Appendix C country list; add `domestic` zone.
- Fill weight tiers (domestic + international), products, services, prices; run `make validate` to confirm schema alignment.
- Add `rules.json` for size/declared-value guards; set `mark_type` / `tracking_mode` on products.
- Wire adapter scaffold (label generation) once data is stable; set SDK config `provider: 'ukrposhta'` for resolution tests.
