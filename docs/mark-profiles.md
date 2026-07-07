# Mark profiles

How franking **graphic footprints** are named and stored in **porto-data**.

**Not the same as `porto_id`.** Product `porto_id` is size-only (`small` … `extra_large`). Service `porto_id` covers add-ons (`registered`, `tracking`, …). `mark_profile` (`domestic`, `international`, …) is **layout output** after zone + services are resolved.

## Three naming layers

| Layer | Where defined | Examples |
|-------|---------------|----------|
| **Carrier native** | `products.json` (`id`), `graph.edges.wire` | `standardbrief`, wire `10001` (Deutsche Post Internetmarke) |
| **Porto `porto_id`** | `schemas/porto_ids.schema.json` | `small` … `extra_large` (product); `registered` (service) |
| **Porto `mark_profile`** | `marks.json` → `profiles[].id` | `domestic`, `registered_international` |

Display-only: `marks.profiles[].label` — operator-facing text in `marks.json`.

## What porto-data contains

| File | Fields |
|------|--------|
| `marks.json` → `profiles[]` | `id`, `mark_type`, `size` (mm), `mime_type` |
| `marks.json` → `calibrations[]` | Optional checkout output dimensions per integration layout variant |
| `marks.json` → `default_profile` | Fallback when `graph.edges.marks` omits a zone |
| `graph.json` → `edges.marks` | Per zone: `profile` + optional `services` overrides |
| `graph.json` → `edges.products` | Product × zone × weight (unchanged) |
| `zones.json` | Zone catalog — every zone id must appear in **`edges.marks`** |
| `services.json` | `porto_id`, features — no mark fields |
| `formats/layouts.json` | Envelope `post_mark` anchor (x/y mm) |

Validators check profile ids, `edges.marks` keys vs `zones.json`, service ids vs `graph.services`, and schema shape.

## `graph.edges` shape

Example (Deutsche Post native ids — other operators use their own `products.json` / `services.json` keys):

```json
"edges": {
  "products": {
    "standardbrief": {
      "zones": ["domestic", "world"],
      "weight_tiers": ["W0020"]
    }
  },
  "marks": {
    "domestic": {
      "profile": "domestic",
      "services": {
        "einschreiben": "registered",
        "einschreiben_einwurf": "registered",
        "einschreiben_rueckschein": "registered"
      }
    },
    "world": {
      "profile": "international",
      "services": {
        "einschreiben": "registered_international"
      }
    }
  }
}
```

**Resolution (consumer):**

1. Read `graph.edges.marks[zone].profile` (else `marks.default_profile`).
2. For each selected native service id, if `edges.marks[zone].services[service_id]` exists → use that profile.
3. Look up `marks.profiles[id].size` and `formats/layouts.json` `post_mark`.
4. When `marks.calibrations[]` is present, use it for integration-specific checkout output size (mm/px at a given dpi).

Service keys are **native ids** from `graph.services` / `services.json`, not `porto_id`.

## Per-provider mark tables

Operator-specific profile matrices, measured sizes, and adapter calibrations live in **`docs/providers/<id>.md`** (not here).

| Provider | Doc |
|----------|-----|
| Deutsche Post | [providers/deutschepost.md](providers/deutschepost.md#mark-profiles--internetmarke-calibrations) |
| La Poste | [providers/laposte.md](providers/laposte.md) |
| Swiss Post | [providers/swisspost.md](providers/swisspost.md) |
| Ukrposhta | [providers/ukrposhta.md](providers/ukrposhta.md) |

## See also

- [resolution.md](resolution.md) — product disambiguation via `graph.edges.products`
- [id.md](id.md) — `porto_id` vocabulary
- `porto_data/schemas/marks.schema.json` · `porto_data/schemas/graph.schema.json`
