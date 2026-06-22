# Mark profiles

How franking **graphic footprints** are named, stored, resolved, and consumed by the SDK.

**Not the same as `porto_id`.** `porto_id` (`small`, `registered`, …) is what the app passes in. `mark_profile` (`domestic`, `international`, …) is what the bundle returns for **layout** after product + zone + services are resolved.

## Three naming layers

| Layer | Who owns it | Examples | SDK uses it for |
|-------|-------------|----------|-----------------|
| **Carrier native** | Operator | `standardbrief`, `einschreiben`, `native_id: 10001`, API product codes | Adapter purchase calls only |
| **Porto `porto_id`** | porto-data enum | `small`, `registered` (service), `extra_large` | **Input** — `resolve({ letterType: "small", … })` |
| **Porto `mark_profile`** | porto-data convention | `domestic`, `international`, `registered`, `registered_international` | **Output** — stamp size + envelope anchor |

Display-only (never ids): `marks.profiles[].label` — e.g. “Internetmarke domestic”, “Mon Timbre en ligne”.

```text
App input                    Bundle resolution                 Layout / adapter
─────────                    ─────────────────                 ────────────────
porto_id: small        →     product_id: standardbrief
zone: world            →     zone: world
services: [registered] →     service_id: einschreiben
                       →     mark_profile: registered_international   ← OUR id
                       →     size: 57×30 mm, mark_type: stamp
                       →     post_mark anchor from layouts.json
                       →     adapter calls Internetmarke with native_id
```

## `mark_profile` ladder (ours — shared across providers)

These ids live in **`providers/<id>/marks.json`** under `profiles[].id`. Same vocabulary everywhere; **sizes differ per provider**.

| `mark_profile` | Meaning |
|----------------|---------|
| `domestic` | Default home-market franking graphic |
| `international` | International destination lane (wider / extra lines) |
| `registered` | Registered **domestic** footprint (taller graphic, service lines) |
| `registered_international` | Registered **international** footprint |

Read as two axes:

1. **Lane** (from zone): `domestic` or `international`
2. **Registered service** (if selected): upgrade to `registered` or `registered_international`

Not every provider defines all four rows. Missing row = that variant does not exist or reuses another (e.g. La Poste MTEL registered uses `domestic` stamp size + paper liasse).

### Do not confuse with `porto_id: registered`

| Field | Layer | Meaning |
|-------|-------|---------|
| `services[].porto_id: "registered"` | SDK **input** | User wants registered-mail add-on |
| `mark_profile: "registered"` | SDK **layout output** | Use domestic registered **stamp footprint** |

Same English word, different namespaces. SDK exposes them on different fields (`service` vs `markProfile`).

## Where data lives

| File | What |
|------|------|
| `providers/<id>/marks.json` | Profile catalog: `id`, `mark_type`, `size` (mm), `mime_type`, human `label` |
| `graph.edges[product_id].mark_profile_by_zone` | Zone → profile for lane (`domestic` vs `international`) |
| `services[].mark_profile` | Service overrides footprint (e.g. DE Einwurf → `registered`) |
| `services[].mark_profile_by_zone` | When registered footprint differs by lane (e.g. DE `einschreiben`) |
| `products.mark_profile` | Rare product-only override (prefer graph zone map) |
| `marks.default_profile` | Fallback — always `domestic` today |
| `formats/layouts.json` | Envelope `post_mark` anchor (placement, not graphic size) |

Provider folder (`deutschepost`, `laposte`, …) scopes everything. There is **no** global `mark_profile` enum file yet — ids are shared **by convention** and validated per provider in CI.

## Resolution order (bundle / SDK)

After `product_id` and `zone` are known, and optional `service_ids[]` are selected:

```text
1. graph.edges[product_id].mark_profile_by_zone[zone]
2. For each selected service (if any has mark profile fields):
     service.mark_profile_by_zone[zone] ?? service.mark_profile
   (service wins over lane — registered upgrades footprint)
3. products.mark_profile
4. marks.default_profile
```

Then lookup `marks.profiles[id].size` and `mark_type`.

### Deutsche Post example

| Facts | `mark_profile` |
|-------|----------------|
| `standardbrief`, zone `domestic`, no services | `domestic` |
| `standardbrief`, zone `world`, no services | `international` |
| `standardbrief`, zone `domestic`, `einschreiben_einwurf` | `registered` |
| `standardbrief`, zone `world`, `einschreiben` | `registered_international` |

## Sizes (nominal mm)

| Provider | domestic | international | registered | registered_international |
|----------|----------|---------------|------------|--------------------------|
| deutschepost | 36×16 | 60×16 | 57×21 | 57×30 |
| laposte | 64×34 | 64×34 | — | — |
| swisspost | 40×40 | 40×40 | — | — |
| ukrposhta | 148×210 (label) | same as domestic (`world` → `domestic` profile) | — | — |

DE from Internetmarke PDF samples. La Poste from Avery L7159 (63.5×33.9 mm, stored as integers). Swiss nominal until WebStamp samples verified.

## SDK contract (target — easy consumption)

App code should **not** read `marks.json` or walk graph edges. The resolver returns one layout block on **`ResolvedData`**:

```typescript
// TypeScript (camelCase)
interface ResolvedMarkLayout {
  markProfile: 'domestic' | 'international' | 'registered' | 'registered_international'
  markType: 'stamp' | 'label'
  widthMm: number
  heightMm: number
  mimeTypes: string[]          // from marks.profiles[].mime_type
  postMark?: { x: number; y: number }  // envelope anchor from formats/layouts.json (mm)
}

interface ResolvedData {
  // … product, zone, pricing …
  markLayout: ResolvedMarkLayout
}
```

```python
# Python (snake_case)
class ResolvedMarkLayout(BaseModel):
    mark_profile: str
    mark_type: Literal["stamp", "label"]
    width_mm: int
    height_mm: int
    mime_types: list[str]
    post_mark: dict[str, int] | None = None  # {x, y} anchor only; size from width_mm/height_mm
```

Graphic footprint size (`width_mm` / `height_mm`) comes from **`marks.profiles[].size`**. Envelope placement uses **`formats/layouts.json`** `post_mark` anchor (`x`, `y` only per `layouts.schema.json`) for the selected `envelope_id` and jurisdiction.

**One resolver call → everything needed to place the graphic.** Adapters still use native `product_id` / API codes for purchase; layout uses `markLayout` only.

Resolver inputs that affect `mark_profile`:

- `provider` (which `marks.json`)
- resolved `product_id`
- resolved `zone`
- selected native `service_ids[]` (not `porto_id` — resolve services first)

## See also

- [resolution.md](resolution.md) — product disambiguation + mark profile order
- [id.md](id.md) — `porto_id` vocabulary (input layer)
- `porto_data/schemas/marks.schema.json`
