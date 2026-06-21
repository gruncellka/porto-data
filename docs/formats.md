# Formats bundle (`porto_data/formats/`)

Shared **letter mail** data used by all operators: physical envelope formats and jurisdiction-specific print/window geometry. Not per-provider tariff data—that lives under `providers/<id>/`.

## Files

| File             | `file_type` | Role                                                                                                                                                                                    |
| ---------------- | ----------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `envelopes.json` | `envelopes` | Canonical envelope **`id`**, face **width/height** (mm), **`standard`** (e.g. ISO 269), **`sheets[]`** (ISO 216 sheet + fold hints).                                                    |
| `layouts.json`   | `layouts`   | Per **ISO 3166-1 alpha-2** jurisdiction (e.g. DE, CH, FR), per envelope **`id`**: print area, address area, window, post mark anchor; optional **`standard`** norm token (e.g. DIN678). |

Physical sizes stay in **`envelopes.json`**; geometry on the face stays in **`layouts.json`**.

## Schemas & mappings

- Schemas: `schemas/envelopes.schema.json`, `schemas/layouts.schema.json`.
- **`mappings.json`** → `mappings.formats` lists schema→data pairs for these files.
- Provider **`graph.json`** `dependencies` reference paths like `formats/envelopes.json` and `formats/layouts.json` where the tariff depends on them.

## Conventions

- Units: **`mm`** for dimensions (see each file’s `unit`).
- Coordinate origin: **top-left**, landscape front of envelope (see schema descriptions).
