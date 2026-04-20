# Porto ID naming policy (letters & services)

**See also:** [Porto ID / native ID mapping tables](../PORTO_ID_MAPPING.md) · [Normalization plan](../porto_id_normalization_plan.md)

Purpose: unify `porto_id` names across providers (letters-only scope) so that size/weight tiers and services are consistent. These are the **canonical** `porto_id` buckets we should converge to; provider `id` and `native_id` stay provider-specific, but `porto_id` should use these names.

## Products (by size/weight role, no prefix)

- `small` — smallest letter/postcard-sized (e.g., DP Standardbrief, La Poste Lettre verte, Swiss A-Post Standardbrief)
- `medium` — mid-step (e.g., DP Kompaktbrief)
- `large` — larger/C4 (~500 g range)
- `extra_large` — up to 1–2 kg letters (maxibrief-like)
- Optional: `postcard` only if explicitly in scope; otherwise fold into `small`.

## Services (no prefix)

- `registered` — registered/track+signature base (Einschreiben, Recommandée, etc.)
- `registered_return_receipt` — registered with return receipt/AR
- `tracking` — tracking add-on (when sold separately from the product)
- `insurance` — additional insurance
- `return_receipt` — standalone AR/return-receipt add-on (when not bundled with registered)
- `proof_of_mailing` / `proof_of_delivery` — only if a carrier sells these as distinct paid add-ons
- Feature names (examples): `tracking_number`, `proof_of_mailing`, `recipient_signature`, `return_receipt`, `proof_of_delivery`. `inventory_description` is a paid service/surcharge, not a feature. `letter_thickness_band` is **not** kept as a feature; thickness surcharges stay in rules (metric-driven), not as services.

## General rules

- Products carry base postage only (no service tiers baked in).
- Services carry surcharges/add-ons; prices belong in `prices/services.json`.
- If a carrier sells “registered tiers” (e.g., R1/R2/R3), prefer modeling as registered + service variant, not separate base products, unless the carrier has distinct SKU codes that must be captured.
- `porto_id` should map to the canonical names above; `id` remains a readable provider label; `native_id` is the carrier’s code/name.
- Drop postcard unless explicitly in scope; remove offline-only/not-orderable services from data (don’t expose in SDK).

## Suggested renames (canonical `porto_id` targets)

- Products:
    - `letter_standard` → `small`
    - `letter_compact` → `medium`
    - `letter_large` → `large`
    - `letter_extra_large` → `extra_large`
    - Drop postcard; fold into `small`.
- Services:
    - `registered_mail` → `registered`
    - `registered_mail_return_receipt` / similar → `registered_return_receipt`
    - `letter_tracking` → `tracking`
    - `additional_insurance` → `insurance`
    - `return_receipt` → `return_receipt`
    - Thickness surcharges remain rule-based; do not model as a service.

## Next steps

- Align each provider’s `porto_id` values to these canonical buckets.
- Verify prices and graph edges remain correct; services stay separate from products.
