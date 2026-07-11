# Product resolution when `porto_id` is ambiguous

SDK and app code should pass **`porto_id`** (canonical bucket). The bundle resolves to a native **`product.id`** using provider context plus shipment facts.

## Inputs

| Input | Role |
|-------|------|
| `provider` | Operator id (`deutschepost`, `ukrposhta`, `laposte`, `swisspost`, …) |
| `porto_id` | Canonical product size bucket (`small`, `large`, …) |
| `zone` | Resolved from destination country |
| `weight` | Shipment weight (unit from `graph.unit.weight` / `weights.json`) → `weight_tier` |
| `services[]` | Optional selected service native ids or porto_ids (SDK layer) |

## Resolution order

1. Filter `products.json` rows where `porto_id` matches and `zones` contains the target zone.
2. Resolve `weight_tier` from `weights.json` for the given `weight`.
3. Intersect with `graph.json` → `edges.products[product_id].zones` and `edges.products[product_id].weight_tiers`.
4. If exactly one product remains, use that `product.id`.
5. If multiple products remain, apply provider-specific disambiguation below.
6. Price lookup uses native `product_id` × `zone` × `weight_tier` in `prices/products.json`.
7. **Delivery hint:** pick the `products.delivery[]` entry whose `zones` contains the shipment `zone`; join with `markets[CC].working_days` from `providers.json` → `country` (see below).
8. **Wire code (online purchase only):** `graph.edges.wire[integration][product_id][zone_id]` — optional `services[service_id]` override when `strategy` is `service` (Deutsche Post Internetmarke). See [Wire resolution](#wire-resolution) below.

When step 4 still leaves multiple products, the SDK or app must apply the provider-specific rules below (or an explicit user/operator hint). The bundle does not encode speed class or registered tier as separate `porto_id` values today.

Cross-file refs (graph, prices, rules) always use **native `id`**, never `porto_id`. See [CONTRIBUTING.md](../CONTRIBUTING.md).

## Delivery hints (operator SLA, zone-scoped)

After native `product.id` is resolved, expose an indicative **`delivery_hint`** for the shipment zone:

1. Find `products.delivery[]` entry where `zones` includes the target **zone**.
2. Resolve market calendar: `providers.json` → `country` → `policy/markets.json` → `markets[CC].working_days`.
3. Merge entry `span`, `days_min` / `days_max`, and weekdays: `entry.weekdays` when set, else `markets[CC].working_days.weekdays`.

| Field | Source |
|-------|--------|
| `span`, `days_*` | `products.delivery[]` row for the zone |
| `working_days.market` | Provider home country (`providers[provider].country`) |
| `working_days.weekdays` | Entry override or `markets[CC].working_days.weekdays` |
| `working_days.exclude_public_holidays` | `markets[CC].working_days.exclude_public_holidays` |

Indicative only — not a guaranteed delivery date. No SDK speed-class enum (`lane`); disambiguation uses native `product.id`, delivery preference, or explicit user choice.

**Coverage:** each product’s `delivery[].zones` must partition `product.zones` exactly (validated in CI).

## Candidate enrichment (resolution facts)

After graph filtering, each remaining candidate carries optional facts for SDK/UI disambiguation (no French name parsing):

| Field | Source | Role |
|-------|--------|------|
| **`delivery_hint`** | `products.delivery[]` + `markets[CC].working_days` | SLA span/days for the shipment zone |
| **`included_features[]`** | `products.included_features` | Capabilities bundled in base postage (refs `features.json` ids) |
| **`indemnity`** | `products.indemnity` | Operator tier code + loss/damage cap (`max.amount` in minor units) |
| **`tracking_mode`** | `products.tracking_mode` | Whether tracking is none / optional / included |

`included_features` lists provider feature **ids** (same namespace as `services[].features`), not priced add-ons from `services.json`. Omit the field when nothing is bundled (e.g. plain Lettre verte).

`indemnity.tier` is operator-native (La Poste R1/R2/R3 today) — not a global Porto enum. `indemnity.max.amount` is in the provider market’s minor units; resolve **currency** from `markets[providers.country].currency` (same as prices).

### Disambiguation matrix

When multiple products share `(porto_id, zone, weight_tier)` after graph filtering:

| Provider / family | Primary axis | Secondary |
|-------------------|--------------|-----------|
| **Swiss Post** A vs B | `delivery[]` fingerprint (span, days) | explicit `product.id` |
| **La Poste** R1/R2/R3 | `indemnity.tier` | price row |
| **La Poste** verte / suivie / Services Plus | `included_features[]`, `tracking_mode` | price row |
| **Deutsche Post** extra_large twins | zone + weight_tier | — |
| **Ukrposhta** small vs large | zone (large is domestic-only) | — |
| **Else** | explicit native **`product.id`** or user preference | — |

CI rejects twins that share the same resolution fingerprint (`delivery` sig per zone, `indemnity.tier`, `included_features`, `tracking_mode`) for the same graph edge key.

## Known ambiguous cases

### Deutsche Post — extra_large variants

`maxibrief` and `maxibrief_ausland` both map to `extra_large`.

Disambiguation is **deterministic** from **zone + weight_tier** (not user choice):

| Weight (g) | Tier | Zone | Resolves to |
|------------|------|------|-------------|
| 501–1000 | W1000 | `domestic`, `zone_1_eu`, `zone_2_europe`, `world` | `maxibrief` |
| 1001–2000 | W2000 | `zone_1_eu`, `zone_2_europe`, `world` | `maxibrief_ausland` |
| 1001–2000 | W2000 | `domestic` | *(no product — `maxibrief_ausland` is abroad-only)* |

`maxibrief_ausland` never appears in `domestic` zone, so `extra_large` + DE is never ambiguous. BDD and adapter matrices should use **501 g** for `maxibrief` (W1000) and **1001 g** (or higher in W2000) for `maxibrief_ausland` — not 500 g (W0500, `grossbrief` tier).

### Ukrposhta — `small` vs `large` (letters only)

| `porto_id` | `product.id` | Zones | Disambiguation |
|------------|--------------|-------|----------------|
| `small` | `lyst_standartnyi` | `domestic`, `world` | Default letter; all international letter postage |
| `large` | `dokument` | `domestic` only | Flat domestic “Документ” letter (≤1 kg); never international |

If `porto_id: large` is requested for a non-domestic zone, resolution fails — use `small`. Parcels and non-letter Ukrposhta SKUs are out of bundle scope.

### La Poste — registered letter tiers

Several products share `porto_id: small` (`lettre_verte`, `lettre_recommandee_r_un`, `r_deux`, `r_trois`, international variants, …).

Disambiguation: **native product id** and **`indemnity.tier`** (R1/R2/R3), not `porto_id` alone. Recommandée is a distinct product SKU at the same letter size — not a `registered` service add-on like Deutsche Post Einschreiben. Compare **`included_features[]`** and price when choosing verte vs suivie vs Services Plus.

### Swiss Post — same `porto_id`, different speed class

Multiple products share `porto_id: small` or `large`:

- `a_post_standardbrief` vs `b_post_standardbrief` (domestic speed)
- `international_standardbrief` vs domestic variants

Disambiguation: prefer **zone** (domestic vs international) first, then compare **delivery hints** (`span`, `days_max`) or explicit **native `product.id`** when the user selects a tariff (e.g. A-Post vs B-Post).

## Service variants

Multiple `services[].id` rows may share one `porto_id` (e.g. two `registered` variants on Deutsche Post). SDK should select by native service id or operator-specific option once the user picks a variant.

## Mark profile resolution

Lane and service mark mapping: **`graph.edges.marks[zone]`**. Catalog sizes: **`marks.json`** → `profiles[]`. See [marks.md](marks.md).

## Wire resolution

Stage 2 of the SDK pipeline — after native `product.id`, `zone`, and optional `service_ids[]` are known:

| Step | Graph field | SDK |
|------|-------------|-----|
| Load strategy | `graph.strategy` | resolution contract for stage 1 |
| Base adapter code | `graph.edges.wire[integration][product_id][zone_id].base` | `resolve_wire_code(...)` |
| Service override (DE only) | `...services[service_id]` | when `strategy: service` |

### `graph.strategy` per provider

| Provider | Strategy | Wire integration | Wire shape |
|----------|----------|------------------|------------|
| Deutsche Post | `service` | `internetmarke` | `base` + optional `services` map |
| La Poste | `id` | `mon_timbre_en_ligne` | `base` = `products.id` (purchasable catalog key) |
| Swiss Post | `speed` | `webstamp` | `base` = `products.id` until Options API harvest |
| Ukrposhta | `min` | `ukrposhta_ecom` | `base` only (`letter` / `document`) |

**La Poste `strategy: id`:** each `products.id` is a distinct purchasable product line (Lettre verte, R1–R3, …). `porto_id: small` is a coarse cross-provider size bucket only — resolution requires explicit `products.id` (or indemnity tier). Wire `base` must equal `products.id`.

Adapter wire codes live in **`graph.edges.wire` only** — not on `products.json` or `services.json` rows. Validators reject `native_id`, `zone_native_ids`, and `product_native_ids` on entity files.

Lookup rules (SDK):

1. No selected services → use `.base`.
2. `service` + one or more service ids → last matching entry in `services` map wins (mirrors `edges.marks` override order).
3. Missing or `null` base → fail closed.

**La Poste / Swiss Post wire keys:** until operator API SKUs are harvested, `base` is the stable **`product.id` string** (catalog key). Adapters resolve catalog keys to live MTEL / WebStamp `post_product_number` via Options harvest or runtime lookup — same pattern as Ukrposhta `"letter"` / `"document"` keys.

## Currency and VAT

Resolve the provider’s market from `providers.json` → `country` → `policy/markets.json` → `markets[CC]`.

| Field | Resolution |
|-------|------------|
| **Currency** | `row.currency` → `prices/*.json` `unit.currency` → `markets[CC].currency` |
| **VAT** | `markets[CC].vat` (`rate`, `exempt`, `domestic.inclusive`, `international.inclusive`) |
| **International row currency** | Must be listed in `markets[CC].international_currency` when it differs from file default |

`graph.json` `unit.currency` mirrors `markets[CC].currency` (validated in CI). Row-level `currency` is only for international tariff rows (e.g. Ukrposhta `world` zone in USD while file default is UAH).

## See also

- [id.md](id.md) — canonical `porto_id` vocabulary
- [porto_id.md](porto_id.md) — live id → porto_id tables
- `porto_data/schemas/porto_ids.schema.json` — enum source of truth
