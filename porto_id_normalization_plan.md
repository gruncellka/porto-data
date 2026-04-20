# Porto ID Normalization Plan (letters & services)

**See also:** [Canonical naming policy](docs/id.md) · [ID mapping tables](PORTO_ID_MAPPING.md)

Goal: align all providers to a canonical `porto_id` set (letters-only scope), keep products vs services separate, and remove redundant features/products.

## Canonical `porto_id` targets (no prefixes)
- Products: `small`, `medium`, `large`, `extra_large` (drop postcard; fold into `small`).
- Services: `registered`, `registered_return_receipt`, `tracking`, `insurance`, `return_receipt`, `thickness`.
- Features: keep `tracking_number`, `proof_of_mailing`, `recipient_signature`, `return_receipt`, `proof_of_delivery`, `inventory_description`; drop `letter_thickness_band` (handled via rule + service price).

## Provider-specific actions

### Deutsche Post
- Products: rename porto_id
  - `letter_standard` → `small`
  - `letter_compact` → `medium`
  - `letter_large` → `large`, `letter_extra_large` → `extra_large`
  - Remove postcard product (postkarte) and its prices/edges.
- Services: rename porto_id
  - `registered_mail` → `registered`
  - `registered_mail_mailbox` → `registered` (variant)
  - `registered_mail_return_receipt` → `registered_return_receipt`
  - `additional_insurance` → `insurance`.
- Features: keep, no change.
- Do not add counter-only add-ons (e.g., Eigenhändig) unless confirmed available via Internetmarke/API.
- Update prices/products, graph edges, services prices as needed.

### La Poste
- Products: split registered tiers into services (or keep as products only if SKU requires)
  - Base letters: map to `small` / `large` as appropriate.
  - Registered R1/R2/R3 (domestic/int’l): move to services or normalize porto_id to `registered` / `registered_return_receipt`.
- Services: rename porto_id
  - Tracking add-on → `tracking`
  - Return receipt → `return_receipt`.
- Features: keep, no change.
- Update prices/products, services, graph accordingly.

### Swiss Post
- Products: map to `small` / `large` / `extra_large` (intl/domestic).
- Services: keep `tracking`; thickness handled as a surcharge via rule + `thickness` service price.
- Features: drop `letter_thickness_band` (rule + surcharge covers it). Keep tracking.
- Update mapping doc after removal.

### Ukrposhta
- Products: already unified to one letter (`letter_standard`) and document; rename porto_id to `small` / `large` if desired.
- Services: rename porto_id
  - `registered_mail` → `registered`
  - `return_receipt` → `return_receipt`
  - Drop `inventory_description_*` if the API does not support fully online attestation (branch-only service).
  - Drop `personal_delivery` if API cannot flag it fully online.
  - `recipient_signature` stays as feature and service outcome.
- Features: keep (tracking absent; signature/return receipt remain; drop inventory_description feature if service removed).

## Cross-cutting
- Update [PORTO_ID_MAPPING.md](PORTO_ID_MAPPING.md) and [docs/id.md](docs/id.md) after renames/removals.
- Ensure `graph.json` edges and `prices/*.json` reflect renamed product_ids/porto_ids.
- Remove postcard prices/edges for Deutsche Post.
- Confirm services vs products separation: registered tiers and AR should be services unless the carrier mandates product SKUs.
- Remove offline-only / not-orderable services entirely (do not keep them in services/prices or expose in SDK surface); includes `inventory_description` if branch-only and `personal_delivery` if counter-only.
- Regenerate metadata after changes.
