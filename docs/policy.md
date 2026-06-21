# Policy bundle (`porto_data/policy/`)

Shared **regulatory and geographic policy** data: legal/sanctions-style restrictions and bloc/country jurisdiction metadata. Operator **operational** limits (conflict rules, infrastructure) live in **`providers/<id>/limits.json`**, not here.

## Files

| File                 | `file_type`     | Role                                                                                                                                                    |
| -------------------- | --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `jurisdictions.json` | `jurisdictions` | EU/UN membership sets, per-country rows, **IANA `timezone`** where used for policy interpretation.                                                      |
| `markets.json`       | `markets`       | Per-country **currency**, **VAT**, and **`intl_ccy`**; resolved via `providers.json` → `country`.                                                         |
| `restrictions.json`  | `restrictions`  | Destination-oriented restrictions; row-level **`effective_from` / `effective_to`**; not carrier-specific execution rules. |

## Schemas & mappings

- Schemas: `schemas/jurisdictions.schema.json`, `schemas/markets.schema.json`, `schemas/restrictions.schema.json`.
- **`mappings.json`** → `mappings.policy` lists schema→data pairs for these files.
- SDKs merge **restrictions** with per-provider **limits** into one restriction surface where applicable. Volatile ops (strikes, live suspensions) belong in SDK runtime overlays — not necessarily in static JSON.

## Conventions

- Country codes: **ISO 3166-1 alpha-2** where a country is referenced.
- Framework/jurisdiction keys follow the schema (e.g. blocs `EU` / `UN`, national codes for sanctions).
