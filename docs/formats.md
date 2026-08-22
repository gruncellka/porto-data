# Formats bundle (`porto_data/formats/`)

Shared **letter mail** data used by all operators: physical envelope formats, jurisdiction-specific print/window geometry, and jurisdiction address forms. Not per-provider tariff data—that lives under `providers/<id>/`.

## Files

| File             | `file_type` | Role                                                                                                                                                                                    |
| ---------------- | ----------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `envelopes.json` | `envelopes` | Canonical envelope **`id`**, face **width/height** (mm), **`standard`** (e.g. ISO 269), **`sheets[]`** (ISO 216 sheet + fold hints).                                                    |
| `layouts.json`   | `layouts`   | Per **ISO 3166-1 alpha-2** jurisdiction (e.g. DE, CH, FR), per envelope **`id`**: factual **`window`**, **`post_mark`** anchor; optional **`standard`** norm token (e.g. DIN678). Addressing/print composition is app/SDK — not catalog fields. |
| `addresses.json` | `addresses` | Sparse per-jurisdiction address forms: **`standard`**, **`postal_code.pattern`**, **`forms[]`** (`street` / `post_box` kinds with `required` fields); optional **`max_line_length`**. |

Physical sizes stay in **`envelopes.json`** (`ISO269`). Face geometry stays in **`layouts.json`**. Address **forms** stay in **`addresses.json`** — not compose zones and not provider wire encoding.

**Sparse jurisdictions:** only countries with cited postal facts appear under `addresses.jurisdictions`. Unknown country codes skip form checks in the SDK (zone/sanctions still apply). Not a world directory.

**Standards:** when `layouts.jurisdictions[CC]` exists, address `standard` matches that layout token (`DIN678`, `SN010130`, `NFZ10011`). UA is address-only today (`UKRPOSHTA`) until measurable `layouts.UA` exists.

**Form kinds:** each jurisdiction lists one or more of `street` and `post_box`. An address uses exactly one kind (post box XOR street line).

## Schemas & mappings

- Schemas: `schemas/envelopes.schema.json`, `schemas/layouts.schema.json`, `schemas/addresses.schema.json`.
- **`mappings.json`** → `mappings.formats` lists schema→data pairs for these files.
- Provider **`graph.json`** `dependencies` reference paths like `formats/envelopes.json`, `formats/layouts.json`, and `formats/addresses.json` where the tariff depends on them.

## Conventions

- Units: **`mm`** for dimensions (see each file’s `unit`).
- Coordinate origin: **top-left**, landscape front of envelope (see schema descriptions).
- Address form keys: uppercase ISO 3166-1 alpha-2; must exist in `policy/jurisdictions.json`.
