# Provider template

Every operator in `porto_data/providers/<id>/` follows this layout. Registry id must match folder name, `providers.json`, and `mappings.json`.

## Required files (all providers)

| Schema | Data path | `file_type` |
|--------|-----------|-------------|
| `marks.schema.json` | `marks.json` | `marks` |
| `products.schema.json` | `products.json` | `products` |
| `features.schema.json` | `features.json` | `features` |
| `services.schema.json` | `services.json` | `services` |
| `product_prices.schema.json` | `prices/products.json` | `product_prices` |
| `service_prices.schema.json` | `prices/services.json` | `service_prices` |
| `zones.schema.json` | `zones.json` | `zones` |
| `weights.schema.json` | `weights.json` | `weights` |
| `limits.schema.json` | `limits.json` | `limits` |
| `graph.schema.json` | `graph.json` | `graph` |

`mappings.json` → `mappings.providers.<id>` must list all required schema→path pairs. CI enforces this via mappings validation.

## Optional files

| Schema | Data path | When |
|--------|-----------|------|
| `rules.schema.json` | `rules.json` | Metric-band conditional surcharges (e.g. Swiss Post thickness). `file_type`: `provider_rules`. |

## Shared bundle dependencies

Provider `graph.json` → `dependencies` may reference:

- `policy/restrictions.json`, `policy/jurisdictions.json`, `policy/markets.json`
- `formats/envelopes.json`, `formats/layouts.json`

## Adding a provider

1. Add entry to `porto_data/providers.json`.
2. Add `mappings.providers.<id>` block with all required schemas.
3. Create `porto_data/providers/<id>/` with JSON files above.
4. Run `make validate` and `make metadata`.

## Identity conventions

- **`label`** — short display name in `providers.json` (UI / prose).
- **`name`** — registered legal entity in `providers.json`.
- **`id`** — native catalog key (operator-flavored snake_case); used in graph, prices, rules.
- **`porto_id`** — canonical SDK bucket; enum in `schemas/porto_ids.schema.json`.
- **`native_id`** — carrier API code when known.

See [CONTRIBUTING.md](../CONTRIBUTING.md) and [id.md](id.md).

## Zone field names

| Entity | Field | Role |
|--------|-------|------|
| **products** | `zones[]` | Destination lanes where the product row applies |
| **services** | `supported_zones[]` | Lanes where the service is orderable via API (may be narrower than product) |

Products were renamed from `supported_zones` → `zones` in the multi-provider layout; services keep `supported_zones` (schema-stable).

## Mark profiles on graph edges

Set **`graph.edges[product_id].mark_profile_by_zone`** explicitly for every zone on that edge when the lane→profile mapping is known (do not rely only on `marks.default_profile`). Registered footprint overrides stay on **`services[].mark_profile`** / **`mark_profile_by_zone`**. See [mark-profiles.md](mark-profiles.md).
