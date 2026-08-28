# Mark profiles

How franking **graphic footprints** are named and stored in **porto-data**.

**Not the same as `kind`.** Products have no `kind`. Service/feature `kind` covers cross-provider grouping (`registered`, `tracking`, …). `mark_profile` (`domestic`, `international`, …) is **layout output** after zone + services are resolved.

## Three naming layers

| Layer | Where defined | Examples |
|-------|---------------|----------|
| **Catalog `id`** | `products.json` (`id`), `services.json` (`id`) | `standardbrief`, `einschreiben` |
| **Wire code** | `graph.edges.wire` | `10001` (Deutsche Post Internetmarke) |
| **Porto `kind`** | `schemas/kinds.schema.json` | `registered` (service); `tracking` (feature) |
| **Porto `mark_profile`** | `marks.json` → `profiles[].id` | `domestic`, `registered_international` |

Display-only: `marks.profiles[].label` — operator-facing text in `marks.json`.

## What porto-data contains

| File | Fields |
|------|--------|
| `marks.json` → `profiles[]` | `id`, `type` (`stamp` \| `label`), `size` (mm), `mime_type`; optional `requires`; optional `clearance` (mm around the graphic) |
| `marks.json` → `placement.envelopes` | Allowed franking **area** per envelope `id` (`x`, `y`, `width`, `height` mm, origin top-left). Omit when the operator has no envelope-face zone (e.g. Ukrposhta eCom label). |
| `marks.json` → `calibrations[]` | Optional checkout output dimensions: `wire` × `mark_profile` (provider layout token) × dpi; franking sizes keyed by Porto profile id in `by_mark_profile`. Measured from real order artifacts — not placement, not clearance. |
| `marks.json` → `default_profile` | Fallback when `graph.edges.marks` omits a zone |
| `graph.json` → `edges.marks` | Per zone: `profile` + optional `services` overrides |
| `graph.json` → `edges.products` | Product × zone × weight (unchanged) |
| `zones.json` | Zone catalog — every zone id must appear in **`edges.marks`** |
| `services.json` | `kind`, features — no mark fields |
| `formats/layouts.json` | Envelope **window** facts only — not mark placement |

Validators check profile ids, `edges.marks` keys vs `zones.json`, service ids vs `graph.services`, and schema shape.

## `graph.edges` shape

Example (Deutsche Post catalog ids — other operators use their own `products.json` / `services.json` keys):

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

**Resolution:**

1. Read `graph.edges.marks[zone].profile` (else `marks.default_profile`).
2. For each selected catalog service `id`, if `edges.marks[zone].services[service_id]` exists → use that profile.
3. Look up `marks.profiles[id].size` and, when present, `marks.placement.envelopes[envelope_id]`. Missing placement stays missing (do not infer it from another provider or from `layouts.json`).
4. When `marks.calibrations[]` is present, use it for wire-specific checkout output size (mm/px at a given dpi) — not as envelope composition.

Service keys are catalog **`id`** values from `graph.services` / `services.json`, not `kind`.

**`requires` on profiles:** stamp / franking-zone profiles do not require addresses; label / address-zone profiles may list `ADDRESS_*`. Registered / Einschreiben does **not** by itself imply address requirements — see [deutschepost.md](providers/deutschepost.md#addresses-vs-mark-profile-cis-r-202802) (CIS R-202802).

**Independent facts:** missing `placement` is not missing jurisdiction window geometry. Ukrposhta eCom has a label size and no envelope-face zone; UA windows live in `layouts.UA` (DSTU 3876-99). Do not invent a draw origin from size + zone — placement is not derived that way in the catalog.

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
- [id.md](id.md) — catalog identity and `kind` vocabulary
- `porto_data/schemas/marks.schema.json` · `porto_data/schemas/graph.schema.json`
