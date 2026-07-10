# Porto ID naming policy (letters & services)

**See also:** [porto_id.md](porto_id.md) (live tables) · [resolution.md](resolution.md) (disambiguation) · [identity.md](identity.md) (full id/name diagram) · `porto_data/schemas/porto_ids.schema.json` (enum source of truth)

Purpose: unify `porto_id` names across providers (letters-only scope) so that size/weight tiers and services are consistent. Provider native `id` and `native_id` stay operator-specific; **`porto_id` is the SDK normalization identifier**.

## Products (by size/weight role, no prefix)

- `small` — smallest letter/postcard-sized (e.g., DP Standardbrief, La Poste Lettre verte, Swiss A-Post Standardbrief)
- `medium` — mid-step (e.g., DP Kompaktbrief)
- `large` — larger/C4 (~500 g range); on Ukrposhta, **only** `dokument` (domestic flat document letter, ≤1 kg) — not used for international rows
- `extra_large` — up to 1–2 kg letters (maxibrief-like)
- `postcard` — only when explicitly in scope; otherwise fold into `small`

## Services (no prefix)

- `registered` — registered/track+signature **service** add-on (e.g. DE Einschreiben, UA intl registered surcharge). La Poste recommandée is a **product** at `porto_id: small`, not this service token.
- `registered_return_receipt` — registered with return receipt/AR
- `tracking` — tracking add-on (when sold separately from the product)
- `insurance` — additional insurance
- `return_receipt` — standalone AR/return-receipt add-on (when not bundled with registered)
- `thickness` — thickness surcharge as a priced **service** line (Swiss Post); **rules** (`rules.json`) decide when it attaches
- `proof_of_mailing` / `proof_of_delivery` — only if a carrier sells these as distinct paid add-ons

## Features (capability vocabulary)

- `tracking_number`, `proof_of_mailing`, `recipient_signature`, `return_receipt`, `proof_of_delivery`
- `thickness_surcharge` — Swiss Post thickness capability on the feature row; **`thickness`** on the service row

## Provider notes (Ukrposhta — letters only)

| `porto_id` | Native product | Zones | Role |
|------------|----------------|-------|------|
| `small` | `lyst_standartnyi` | `domestic`, `world` | Standard letter; all international letter weight tiers |
| `large` | `dokument` | `domestic` only | Ukrposhta “Документ” flat domestic document letter |

No `medium` or `extra_large` **product** rows for Ukrposhta. International registered is a **service** (`mizhnarodne_zareiestrovane` → `porto_id: registered`).

## General rules

- Products carry base postage only and use **size** `porto_id` buckets (`small` … `extra_large`). Registered / recommandée / Einschreiben semantics come from **native product id**, **services**, or **features** — not a separate product `porto_id`.
- Services carry surcharges/add-ons; prices belong in `prices/services.json`.
- Multiple native `id` rows may share one `porto_id`; see [resolution.md](resolution.md).
- **`porto_id` values must match the enum in `porto_ids.schema.json`.** Extend the enum only with semver-major review.

## Reference direction (summary)

| Layer | Identifier |
|-------|------------|
| SDK / app input | `porto_id` |
| graph, prices, rules | native `id` |
| Carrier API | `native_id` |

Full rules: [CONTRIBUTING.md](../CONTRIBUTING.md).
