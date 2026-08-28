# Formats bundle (`porto_data/formats/`)

Shared **letter mail** data used by all operators: physical envelope formats, shared/jurisdiction-standard window geometry, and jurisdiction address forms. Not per-provider tariff data—that lives under `providers/<id>/`.

## Files

| File             | `file_type` | Role                                                                                                                                                                                    |
| ---------------- | ----------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `envelopes.json` | `envelopes` | Canonical envelope **`id`**, face **width/height** (mm), **`standards[]`** (e.g. ISO 269 and DIN 678 on the same face), **`sheets[]`** (ISO 216 sheet + fold hints). |
| `layouts.json`   | `layouts`   | Per **ISO 3166-1 alpha-2** jurisdiction (DE, CH, FR, UA, …), per envelope **`id`**: factual **`window`** size/position; optional **`standard`** norm token (e.g. DIN678, DSTU3876). Keyed by jurisdiction for lookup; facts may come from a **shared** window standard (e.g. DIN 680). Not a “national-only” dump. Mark placement is **not** here. Addressing composition is outside this bundle — not catalog fields. |
| `addresses.json` | `addresses` | Sparse per-jurisdiction address forms: **`standard`**, **`postal_code.pattern`**, **`forms[]`** (`street` / `post_box` kinds with `required` field tokens such as `name`, `street`, `house_number`, `post_box`, `postal_code`, **`locality`**, `country_code`); optional **`max_line_length`**. |

Physical **face** sizes stay in **`envelopes.json`**. Shared/jurisdiction-standard **window** geometry stays in **`layouts.json`**. Mark **size** and **placement** stay on the provider **`marks.json`**. Address **forms** stay in **`addresses.json`** — not compose zones and not provider wire encoding.

**Sparse jurisdictions:** only countries with cited postal facts appear under `addresses.jurisdictions`. Unknown country codes have no form row here (zone/sanctions still apply via other files). Not a world directory.

**Standards:** when `layouts.jurisdictions[CC]` exists, address `standard` matches that layout token (`DIN678`, `SN010130`, `NFZ10011`, `DSTU3876`). Envelope face `standards[]` may cite several norms (ISO 269 + DIN 678); that does not copy one jurisdiction’s windows onto another.

**Form kinds:** each jurisdiction lists one or more of `street` and `post_box`. An address uses exactly one kind (post box XOR street line). Place name field is **`locality`** (UPU; not `city`).

## Schemas & mappings

- Schemas: `schemas/envelopes.schema.json`, `schemas/layouts.schema.json`, `schemas/addresses.schema.json`.
- **`mappings.json`** → `mappings.formats` lists schema→data pairs for these files.
- Provider **`graph.json`** `dependencies` reference paths like `formats/envelopes.json`, `formats/layouts.json`, and `formats/addresses.json` where the tariff depends on them.

## Conventions

- Units: **`mm`** for dimensions (see each file’s `unit`).
- Coordinate origin: **top-left**, landscape front of envelope (see schema descriptions).
- Address form keys: uppercase ISO 3166-1 alpha-2; must exist in `policy/jurisdictions.json`.
