# Product resolution

Catalog **`product.id`** is selected from provider context, destination zone, weight, optional envelope filter, and optional explicit product pin. There is no cross-provider product size taxonomy — see [id.md](id.md).

## Inputs

| Input | Role |
|-------|------|
| `provider` | Operator id (`deutschepost`, `ukrposhta`, `laposte`, `swisspost`, …) |
| `zone` | Resolved from destination country |
| `weight` | Shipment weight (unit from `graph.unit.weight` / `weights.json`) → `weight_tier` |
| `envelope_id` | Optional physical fit filter on `envelope_ids[]`. Absent = no constraint. Present = drop incompatible products. Never selects among remaining rows. Empty `envelope_ids[]` currently matches any envelope. |
| `product_id` | Optional explicit pin to catalog `products.id` |
| `services[]` | Optional requested service **kinds** (intent). Never catalog ids. |
| `service_ids[]` | Optional pins to catalog `services.id` among options for those kinds |

## Resolution order

1. Filter `products.json` rows whose `zones` contains the target zone.
2. When `envelope_id` is present, keep rows whose `envelope_ids[]` includes it (filter only).
3. When `product_id` is pinned, select that row (must still match zone, envelope filter, and graph).
4. Resolve `weight_tier` from `weights.json` for the given `weight`.
5. Intersect with `graph.json` → `edges.products[product_id].zones` and `edges.products[product_id].weight_tiers`.
6. If exactly one product remains, use that `product.id`.
7. If multiple products remain, apply provider-specific disambiguation below.
8. Price lookup uses catalog `product_id` × `zone` × `weight_tier` in `prices/products.json`.
9. **Delivery hint:** pick the `products.delivery[]` entry whose `zones` contains the shipment `zone`; join with `markets[CC].working_days` from `providers.json` → `country` (see below).
10. **Wire code (online purchase only):** when `execution.json` exists, `execution.wire` selects the active **`edges.wire`** channel; then `graph.edges.wire[wire][product_id][zone_id]` — optional `services[service_id]` override when `strategy` is `service` (Deutsche Post Internetmarke). See [Wire resolution](#wire-resolution) below.

When step 7 still leaves multiple products, apply the provider-specific rules below (or an explicit user/operator hint). The bundle does not encode speed class or registered tier as separate product kinds.

Cross-file refs (graph, prices, rules) always use catalog **`id`**, never `kind`. See [CONTRIBUTING.md](../CONTRIBUTING.md).

## Delivery hints (operator SLA, zone-scoped)

After catalog `product.id` is resolved, expose an indicative **`delivery_hint`** for the shipment zone:

1. Find `products.delivery[]` entry where `zones` includes the target **zone**.
2. Resolve market calendar: `providers.json` → `country` → `policy/markets.json` → `markets[CC].working_days`.
3. Merge entry `span`, `days_min` / `days_max`, and weekdays: `entry.weekdays` when set, else `markets[CC].working_days.weekdays`.

| Field | Source |
|-------|--------|
| `span`, `days_*` | `products.delivery[]` row for the zone |
| `working_days.market` | Provider home country (`providers[provider].country`) |
| `working_days.weekdays` | Entry override or `markets[CC].working_days.weekdays` |
| `working_days.exclude_public_holidays` | `markets[CC].working_days.exclude_public_holidays` |

Indicative only — not a guaranteed delivery date. No speed-class enum (`lane`); disambiguation uses catalog `product.id`, delivery preference, or explicit user choice.

**Coverage:** each product’s `delivery[].zones` must partition `product.zones` exactly (validated in CI).

## Candidate enrichment (resolution facts)

After graph filtering, each remaining candidate carries optional facts for disambiguation (no French name parsing):

| Field | Source | Role |
|-------|--------|------|
| **`delivery_hint`** | `products.delivery[]` + `markets[CC].working_days` | SLA span/days for the shipment zone |
| **`included_features[]`** | `products.included_features` | Capabilities bundled in base postage (refs `features.json` ids) |
| **`indemnity`** | `products.indemnity` | Operator tier code + loss/damage cap (`max.amount` in minor units) |
| **`tracking`** | `products.tracking` | Whether tracking is none / optional / included |

`included_features` lists provider feature **ids** (same namespace as `services[].features`), not priced add-ons from `services.json`. Omit the field when nothing is bundled (e.g. plain Lettre verte).

`indemnity.tier` is operator-native (La Poste R1/R2/R3 today) — not a global Porto enum. `indemnity.max.amount` is in the provider market’s minor units; resolve **currency** from `markets[providers.country].currency` (same as prices).

### Disambiguation matrix

When multiple products share the same `(zone, weight_tier)` after graph filtering:

| Provider / family | Primary axis | Secondary |
|-------------------|--------------|-----------|
| **Swiss Post** A vs B | `delivery[]` fingerprint (span, days) | explicit `product.id` |
| **La Poste** R1/R2/R3 | `indemnity.tier` | price row |
| **La Poste** verte / suivie / Services Plus | `included_features[]`, `tracking` | price row |
| **Deutsche Post** extra_large twins | zone + weight_tier | — |
| **Ukrposhta** standard vs document | zone (`dokument` is domestic-only) | envelope filter / explicit `product.id` |
| **Else** | explicit catalog **`product.id`** or user preference | — |

CI rejects twins that share the same resolution fingerprint (`delivery` sig per zone, `indemnity.tier`, `included_features`, `tracking`) for the same graph edge key.

## Known ambiguous cases

### Deutsche Post — extra_large variants

`maxibrief` and `maxibrief_ausland` both serve the extra-large weight band.

Disambiguation is **deterministic** from **zone + weight_tier** (not user choice):

| Weight (g) | Tier | Zone | Resolves to |
|------------|------|------|-------------|
| 501–1000 | W1000 | `domestic`, `zone_1_eu`, `zone_2_europe`, `world` | `maxibrief` |
| 1001–2000 | W2000 | `zone_1_eu`, `zone_2_europe`, `world` | `maxibrief_ausland` |
| 1001–2000 | W2000 | `domestic` | *(no product — `maxibrief_ausland` is abroad-only)* |

`maxibrief_ausland` never appears in `domestic` zone. Use **501 g** for `maxibrief` (W1000) and **1001 g** (or higher in W2000) for `maxibrief_ausland` — not 500 g (W0500, `grossbrief` tier).

### Ukrposhta — standard letter vs document (letters only)

| `product.id` | Zones | Disambiguation |
|--------------|-------|----------------|
| `lyst_standartnyi` | `domestic`, `world` | Default letter; all international letter postage |
| `dokument` | `domestic` only | Flat domestic “Документ” letter (≤1 kg); never international |

If `dokument` is requested for a non-domestic zone, resolution fails — use `lyst_standartnyi`. Parcels and non-letter Ukrposhta SKUs are out of bundle scope.

### La Poste — registered letter tiers

Several products share zone + weight (`lettre_verte`, `lettre_recommandee_r_un`, `r_deux`, `r_trois`, international variants, …).

Disambiguation: catalog **`product.id`** and **`indemnity.tier`** (R1/R2/R3). Recommandée is a distinct product SKU — not a `registered` service add-on like Deutsche Post Einschreiben. Compare **`included_features[]`** and price when choosing verte vs suivie vs Services Plus.

### Swiss Post — same zone + weight, different speed class

Multiple products may share zone + weight:

- `a_post_standardbrief` vs `b_post_standardbrief` (domestic speed)
- `international_standardbrief` vs domestic variants

Disambiguation: prefer **zone** (domestic vs international) first, then compare **delivery hints** (`span`, `days_max`) or explicit catalog **`product.id`** when the user selects a tariff (e.g. A-Post vs B-Post).

## Service variants

Multiple `services[].id` rows may share one `kind` (e.g. two `registered` variants on Deutsche Post). Pin with `service_ids`; do not map `kind` to one catalog `id`.

## Mark profile resolution

Lane and service mark mapping: **`graph.edges.marks[zone]`**. Catalog sizes: **`marks.json`** → `profiles[]`. See [marks.md](marks.md).

## Wire resolution

After catalog `product.id`, `zone`, and optional `service_ids[]` are known:

| Step | Graph field | Role |
|------|-------------|-----|
| Load strategy | `graph.strategy` | resolution contract for stage 1 |
| Active wire channel | `execution.json` → `wire` (when present) | must match an `edges.wire` key |
| Base adapter code | `graph.edges.wire[wire][product_id][zone_id].base` | checkout catalog key |
| Service override (DE only) | `...services[service_id]` | when `strategy: service` |

### `graph.strategy` per provider

| Provider | Strategy | Wire channel (`execution.wire`) | Wire shape |
|----------|----------|---------------------------------|------------|
| Deutsche Post | `service` | `internetmarke` | `base` + optional `services` map |
| La Poste | `id` | `mon_timbre_en_ligne` | `base` = `products.id` (purchasable catalog key) |
| Swiss Post | `speed` | `webstamp` | `base` = `products.id` until Options API harvest |
| Ukrposhta | `min` | `ukrposhta_ecom` | `base` only (`letter` / `document`) |

**`execution.json`:** optional until an execution adapter ships. When present, `wire` must equal one key under `graph.edges.wire`; `billing[]` / `execution[]` gate **capability tokens** only — wire product codes stay in `edges.wire`.

**La Poste `strategy: id`:** each `products.id` is a distinct purchasable product line (Lettre verte, R1–R3, …). Resolution requires explicit `products.id` (or indemnity tier). Wire `base` must equal `products.id`.

Adapter wire codes live in **`graph.edges.wire` only** — not on `products.json` or `services.json` rows. Validators reject `native_id`, `zone_native_ids`, and `product_native_ids` on entity files.

Lookup rules:

1. No selected services → use `.base`.
2. `service` + one or more service ids → last matching entry in `services` map wins (mirrors `edges.marks` override order).
3. Missing or `null` base → fail closed.

**La Poste / Swiss Post wire keys:** until operator API SKUs are harvested, `base` is the stable **`product.id` string** (catalog key). Live MTEL / WebStamp `post_product_number` mapping is outside this bundle — same pattern as Ukrposhta `"letter"` / `"document"` keys.

## Currency and VAT

Resolve the provider’s market from `providers.json` → `country` → `policy/markets.json` → `markets[CC]`.

| Field | Resolution |
|-------|------------|
| **Currency** | `row.currency` → `prices/*.json` `unit.currency` → `markets[CC].currency` |
| **VAT** | `markets[CC].vat` (`rate`, `exempt`, `domestic.inclusive`, `international.inclusive`) |
| **International row currency** | Must be listed in `markets[CC].international_currency` when it differs from file default |

`graph.json` `unit.currency` mirrors `markets[CC].currency` (validated in CI). Row-level `currency` is only for international tariff rows (e.g. Ukrposhta `world` zone in USD while file default is UAH).

## See also

- [id.md](id.md) — catalog identity and `kind` vocabulary
- [kinds.md](kinds.md) — live id → kind tables
- `porto_data/schemas/kinds.schema.json` — service/feature kind enum source of truth
