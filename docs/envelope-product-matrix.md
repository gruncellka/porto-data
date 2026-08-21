# Envelope × product matrix (real envelopes, not tariff handbook)

Instrument for **real catalog envelopes** and shipment preparation — not a 1:1 operator Preisblatt encyclopedia.

## Agreed model

```text
envelope_ids  → which real catalog envelopes the product works with
graph         → allowed weight_tiers for the product
weights.json  → weight bound (tier → grams)
resolver      → finds product and price
Compose       → only checks selected envelope + weight against the already selected product
```

No absolute packaging mm bands duplicated beside `envelope_ids`.

## How data is linked

```text
formats/envelopes.json          canonical envelope id → face mm
       ▲
       │  envelope_ids[] reference these ids only
       │
providers/<id>/products.json    product.id, envelope_ids[], zones[], …
       │
       │  graph.edges.products[product_id].weight_tiers / zones
       ▼
providers/<id>/graph.json       allowed weight_tiers (+ zones)
       │
       ▼
providers/<id>/weights.json     weight_tier → gram band
providers/<id>/prices/…         price: product_id × zone × weight_tier
```

| Concept | Where | Role |
|---------|--------|------|
| Real envelope | `formats/envelopes.json` | Desk catalog face |
| Allowed envelopes | `products[].envelope_ids` | Membership SoT for envelope fit |
| Allowed weight tiers | `graph.edges.products[].weight_tiers` | Which tiers the product may use |
| Weight bound | `weights.json` | Tier → max grams |
| Product + price | Consumer resolver | Not desk check |
| Sanctions / overlays | `policy/restrictions.json`, `limits.json` | Not packaging |

**Invariant:** every id in `envelope_ids` must exist in `formats/envelopes.json`. Empty `envelope_ids` = no format filter (rare).

## How it is resolved

### Resolver (product + price)

1. `graph ∩ products` → candidates for zone + weight_tier
2. Disambiguate twins (see [resolution.md](resolution.md))
3. Price = `product_id × zone × weight_tier`

### Desk (already selected product)

Against the **already selected** product:

- Envelope: `format_id ∈ product.envelope_ids` — else mismatch (never auto-change envelope)
- Weight: vs max from weights via graph tiers — upgrade or oversized as the consumer defines

Strict envelope fit is membership only.

## Product → envelope_ids matrix (catalog)

Catalog faces: `DL`, `C6`, `C5`, `C4`, `B4`.

### Deutsche Post

| Product | envelope_ids |
|---------|----------------|
| `standardbrief` | DL, C6 |
| `kompaktbrief` | DL, C6 |
| `grossbrief` | C5, C4 |
| `maxibrief` | C5, C4, B4 |
| `maxibrief_ausland` | C5, C4, B4 |

### Swiss Post

| Product | envelope_ids |
|---------|----------------|
| `a_post_standardbrief`, `b_post_standardbrief` | DL, C6, C5 |
| `a_post_grossbrief`, `b_post_grossbrief` | C4, B4 |
| `international_standardbrief` | DL, C6, C5 |
| `international_grossbrief` | C4, B4 |
| `international_maxibrief` | B4 |

### Ukrposhta

| Product | envelope_ids |
|---------|----------------|
| `lyst_standartnyi` | DL, C6, C5, C4 |
| `dokument` | C4, B4 (domestic large — intentional) |

### La Poste

All letter products: DL, C6, C5, C4, B4 (same membership; weight ladder differs via graph).

## Related

- [formats.md](formats.md) — shared envelope catalog
- [resolution.md](resolution.md) — product/price resolution
- [identity.md](identity.md) — id namespaces
