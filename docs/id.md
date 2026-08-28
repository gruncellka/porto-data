# Catalog identity

**See also:** [kinds.md](kinds.md) (live `id` ↔ `kind` tables) · [resolution.md](resolution.md) · [identity.md](identity.md) · `porto_data/schemas/kinds.schema.json`

Every catalog row (product, service, feature) has:

| Field | Role |
|-------|------|
| **`id`** | The only identifier. Concrete, provider-scoped. Graph, prices, wire, and pins use this. |
| **`name`** | Native name — the operator’s original (`Standardbrief`, `Einschreiben`, `Sendungsnummer`). |
| **`label`** | English translation (`Standard Letter`, `Registered mail`, `Tracking number`). |

There is no `porto_id`. Products have no size-bucket taxonomy and no `kind`.

## Services and features: `kind`

`kind` is **cross-provider grouping only**. It is not unique and is not a graph/price key.

Examples:

- `id: einschreiben`, `kind: registered`
- `id: sendungsnummer`, `kind: tracking`

Many-to-one is expected (`einschreiben` and `einschreiben_einwurf` both `registered`). `kind` is intent; matching catalog `id`s are options. Pin with `service_ids` when more than one row matches. Do not map `kind` to a single `id`.

### Service kinds

`registered`, `registered_return_receipt`, `tracking`, `insurance`, `return_receipt`, `thickness`, `acceptance_proof`, `delivery_proof`

La Poste recommandée is a **product** with features/indemnity, not service `registered`.

### Feature kinds

`tracking`, `acceptance_proof`, `recipient_signature`, `return_receipt`, `delivery_proof`, `thickness`

## Products

Country + weight + zone are the core facts. Optional `envelope_id` **filters** `envelope_ids[]` (absent = no constraint; present = drop incompatible rows; never selects among remaining). Selection is via `product_id` / preference / unique remaining row, or ambiguity. Do not invent `small` \| `medium` \| `large` \| `extra_large`.

Ukrposhta: `lyst_standartnyi` and `dokument` are two product ids; filter by envelope/weight/zone, pin with `product_id` — not a size class.

## Reference direction

| Layer | Identifier |
|-------|------------|
| Catalog identity | concrete `id` |
| Cross-provider intent (services/features) | `kind` |
| graph, prices, rules, `services[].features[]` | concrete `id` |
| Carrier API | runtime wire codes (not a catalog field) |

`kind` values must match `kinds.schema.json`. Extend the enum only with semver-major review.

Full rules: [CONTRIBUTING.md](../CONTRIBUTING.md).
