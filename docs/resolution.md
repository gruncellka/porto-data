# Product resolution when `porto_id` is ambiguous

SDK and app code should pass **`porto_id`** (canonical bucket). The bundle resolves to a native **`product.id`** using provider context plus shipment facts.

## Inputs

| Input | Role |
|-------|------|
| `provider` | Operator id (`deutschepost`, `ukrposhta`, `laposte`, `swisspost`, …) |
| `porto_id` | Canonical product bucket (`small`, `registered`, …) |
| `zone` | Resolved from destination country |
| `weight_g` | Actual weight in grams → `weight_tier` via `weights.json` |
| `services[]` | Optional selected service native ids or porto_ids (SDK layer) |

## Resolution order

1. Filter `products.json` rows where `porto_id` matches and `zones` contains the target zone.
2. Resolve `weight_tier` from `weights.json` for the given `weight_g`.
3. Intersect with `graph.json` → `edges[product_id].zones` and `edges[product_id].weight_tiers`.
4. If exactly one product remains, use that `product.id`.
5. If multiple products remain, apply provider-specific disambiguation below.
6. Price lookup uses native `product_id` × `zone` × `weight_tier` in `prices/products.json`.

When step 4 still leaves multiple products, the SDK or app must apply the provider-specific rules below (or an explicit user/operator hint). The bundle does not encode speed class or registered tier as separate `porto_id` values today.

Cross-file refs (graph, prices, rules) always use **native `id`**, never `porto_id`. See [CONTRIBUTING.md](../CONTRIBUTING.md).

## Known ambiguous cases

### Deutsche Post — extra_large variants

`maxibrief` and `maxibrief_international_heavy` both map to `extra_large`.

Disambiguation: **zone** and **weight_tier** (e.g. W2000 only on international heavy).

### Ukrposhta

`lyst_standartnyi` → `porto_id: small`; `dokument` → `porto_id: large`. Currently distinct at the `porto_id` level.

### La Poste — registered letter tiers

Several products use `porto_id: registered` (`lettre_recommandee_r_un`, `r_deux`, `r_trois`, international variants).

Disambiguation: match **registered tier** from user selection or service bundle (R1/R2/R3), not from `porto_id` alone.

### Swiss Post — same `porto_id`, different speed class

Multiple products share `porto_id: small` or `large`:

- `a_post_standardbrief` vs `b_post_standardbrief` (domestic speed)
- `international_standardbrief` vs domestic variants

Disambiguation: prefer **zone** (domestic vs international) first, then **speed class** (A-Post vs B-Post) from app/SDK policy or explicit product hint when the user selects a tariff.

## Service variants

Multiple `services[].id` rows may share one `porto_id` (e.g. two `registered` variants on Deutsche Post). SDK should select by native service id or operator-specific option once the user picks a variant.

## Mark profile data (SDK consumes; not resolved in this repo)

Lane mapping: **`marks.zones[zone]`** in each provider’s **`marks.json`**. Graph edges and services have **no** mark fields. How the Porto SDK composes `markLayout` from zone + services is documented in [mark-profiles.md](mark-profiles.md) § Consumer behavior.

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
