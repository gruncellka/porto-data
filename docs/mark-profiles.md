# Mark profiles

How franking **graphic footprints** are named and stored in **porto-data**. The **Porto SDK** (separate product) reads this data and produces `markLayout` at runtime — not implemented in this repo.

**Not the same as `porto_id`.** `porto_id` (`small`, `registered`, …) is SDK **input**. `mark_profile` (`domestic`, `international`, …) is SDK **layout output** after zone + services are resolved.

## Three naming layers

| Layer | Where defined | Examples |
|-------|---------------|----------|
| **Carrier native** | `products.json`, adapters | `standardbrief`, `native_id: 10001` |
| **Porto `porto_id`** | `schemas/porto_ids.schema.json` | `small`, `registered` (service) |
| **Porto `mark_profile`** | `marks.json` → `profiles[].id` | `domestic`, `registered_international` |

Display-only: `marks.profiles[].label` — e.g. “Internetmarke domestic”.

## What porto-data contains

| File | Fields |
|------|--------|
| `marks.json` → `profiles[]` | `id`, `mark_type`, `size` (mm), `mime_type` |
| `marks.json` → `zones` | One map: `zone_id → profile_id` (lane) |
| `marks.json` → `default_profile` | Fallback when a zone key is missing |
| `zones.json` | Zone catalog — every zone id must appear in **`marks.zones`** |
| `graph.json` → `edges` | Product × zone × weight — **no mark fields** |
| `services.json` | `porto_id`, features — **no mark fields** |
| `formats/layouts.json` | Envelope `post_mark` anchor (x/y mm) |

Validators in this repo check profile ids, `marks.zones` keys vs `zones.json`, and schema shape. **No resolution code.**

## `mark_profile` ladder (shared vocabulary)

| `mark_profile` | Meaning |
|----------------|---------|
| `domestic` | Home-market franking graphic |
| `international` | International lane |
| `registered` | Registered domestic footprint (DE catalog only today) |
| `registered_international` | Registered international footprint (DE only today) |

FR/CH/UA: no separate registered rows — lane size applies until measured.

### Do not confuse with `porto_id: registered`

| Field | Layer |
|-------|-------|
| `services[].porto_id: "registered"` | SDK input — user wants Einschreiben |
| `mark_profile: "registered"` | Layout output — DE stamp footprint id in `marks.json` |

## Consumer behavior (Porto SDK — documented, not coded here)

SDKs that depend on `@gruncellka/porto-data` / `gruncellka-porto-data` should:

1. Read `marks.zones[zone]` (else `default_profile`) for the lane profile id.
2. When a selected service has `porto_id` `registered` or `registered_return_receipt`, upgrade to `registered` / `registered_international` if those profiles exist in `marks.profiles[]`.
3. Look up `marks.profiles[id].size` and `formats/layouts.json` `post_mark` for placement.

Implementation: **porto-sdk-python** / **porto-sdk-typescript** (`UnifiedResolverService`). See SDK docs in the lab monorepo.

### Deutsche Post examples (expected SDK output)

| Zone + services | Profile id |
|-----------------|------------|
| `domestic`, none | `domestic` |
| `world`, none | `international` |
| `domestic`, `einschreiben` | `registered` |
| `world`, `einschreiben` | `registered_international` |

## Sizes (nominal mm)

| Provider | domestic | international | registered | registered_international |
|----------|----------|---------------|------------|--------------------------|
| deutschepost | 36×16 | 60×16 | 57×21 | 57×30 |
| laposte | 64×34 | 64×34 | same as lane | same as lane |
| swisspost | 40×40 | 40×40 | same as lane | same as lane |
| ukrposhta | 148×210 (label) | same as domestic (`world` → `domestic`) | — | — |

DE sizes from Internetmarke PDF samples (not official spec).

## See also

- [resolution.md](resolution.md) — product disambiguation (SDK concern; data rules in graph)
- [id.md](id.md) — `porto_id` vocabulary
- `porto_data/schemas/marks.schema.json`
