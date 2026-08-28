# Policy bundle (`porto_data/policy/`)

Shared **geographic and destination-restriction** data plus bloc/country jurisdiction metadata.

## Files

| File                 | `file_type`     | Role                                                                                                                                                    |
| -------------------- | --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `jurisdictions.json` | `jurisdictions` | EU/UN membership sets, per-country rows, **IANA `timezone`** where used for policy interpretation.                                                      |
| `markets.json`       | `markets`       | Per-country fiscal defaults (`currency`, `vat`, `international_currency`, `settlement`) and **`working_days`** (postal calendar). Currency/VAT resolution: [resolution.md](resolution.md). |
| `restrictions.json`  | `restrictions`  | Durable destination facts in country-keyed `legal` and `routing` maps. No record id. Legal regions require `jurisdictions` keyed by `jurisdictions.json` identifiers (`EU` \| `CH` \| `UA`) to instrument arrays (`reference`, `effective_from`, optional `effective_to`). Routing keeps `authority` / `reference` / `reason` / `description`. Machine impact (`block` \| `warn`) is resolved by the SDK into a flat result. |

Provenance / research (why destinations entered or stayed out of the shipped catalog): [restrictions.md](restrictions.md). Research scaffold only — not a catalog and not permission to change `restrictions.json` automatically.

## Schemas & mappings

- Schemas: `schemas/jurisdictions.schema.json`, `schemas/markets.schema.json`, `schemas/restrictions.schema.json`.
- **`mappings.json`** → `mappings.policy` lists schema→data pairs for these files.
- Volatile ops (strikes, live suspensions) do not belong in static JSON.

## Conventions

- Country codes: **ISO 3166-1 alpha-2** where a country is referenced.
- Restriction domains: **`legal`** and **`routing`** only — objects keyed by **ISO 3166-1 alpha-2**. Region keys: **ISO 3166-2**. `partial: true` is optional and emitted only when true in the catalog.
- **`legal`:** Jurisdiction map keys: **`EU`**, **`CH`**, **`UA`** (identifiers from `jurisdictions.json`). Catalog legal rows carry `jurisdictions`, optional `partial`, and short neutral `reason` / `description` (human summary; `reference` stays authoritative). Consumers do not pick the jurisdiction.
- **`routing`:** Recipient country → region. Routing may keep `authority`, `reference`, `reason`, and `description`. Provider jurisdiction is irrelevant unless a routing record explicitly establishes otherwise.
- Machine impact (`block` \| `warn`) is resolved by the consumer SDK from these catalog facts — not stored in the catalog.
- This file is durable destination rules. Live operator incidents are not stored here.
