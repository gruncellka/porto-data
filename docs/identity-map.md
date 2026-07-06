# Identity map — names, ids, variables, relations

One-page map of **who names what** across **porto-data** (JSON + schemas), **Porto SDK** (separate product), and **carrier APIs**.

**porto-data** ships facts and validates them. **Porto SDK** loads the bundle and resolves. This repo has no resolver implementation.

**See also:** [id.md](id.md) · [mark-profiles.md](mark-profiles.md) · [resolution.md](resolution.md) · [SDK_ARCHITECTURE.md](../../docs/sdks/SDK_ARCHITECTURE.md)

---

## Layer stack

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│  APPLICATION                                                                 │
│  vars: provider, destination country, weight_g, letterType, service picks   │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼─────────────────────────────────────────┐
│  PORTO SDK (Python / TypeScript)                                             │
│  input:  porto_id, country_code, weight, service porto_ids                  │
│  output: ResolvedData (+ PortoMark after adapter call)                       │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │ reads bundle only via loader/resolvers
┌───────────────────────────────────▼─────────────────────────────────────────┐
│  PORTO-DATA (this repo — published JSON + schemas)                            │
│  providers/<id>/…  policy/…  formats/…  schemas/…  validators (repo only)   │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │ adapters only
┌───────────────────────────────────▼─────────────────────────────────────────┐
│  CARRIER APIs (Internetmarke, MTEL, WebStamp, Ukrposhta eCom, …)             │
│  native product codes, PDF/PNG bytes, tracking numbers                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Identifier cheat sheet

| Name | Owner | Example | Used in | Never used in |
|------|-------|---------|---------|---------------|
| **`provider`** | Porto registry | `deutschepost` | SDK context, folder path | graph price keys |
| **`label` / `name`** | Display / legal | `"Deutsche Post"`, `"Deutsche Post AG"` | UI, docs | resolution |
| **`country`** | Registry → markets | `DE`, `FR`, `UA`, `CH` | VAT, currency, layouts | product id |
| **`porto_id`** (product) | Porto enum | `small`, `medium`, `large`, `extra_large`, `postcard` | **SDK input** | graph, prices |
| **`porto_id`** (service) | Porto enum | `registered`, `insurance` | **SDK input** | graph.services list |
| **`porto_id`** (feature) | Porto enum | `tracking_number` | semantics | prices |
| **`id`** (product/service) | Provider native | `standardbrief`, `einschreiben` | **graph, prices, rules** | SDK input |
| **`wire_code`** | Graph wire edge | `10001`, `"letter"` | **adapter API only** | products/services rows |
| **`zone`** | Provider | `domestic`, `world`, `zone_1_eu` | prices, graph edges | porto_id |
| **`weight_tier`** | Provider | `W0020`, `W1000` | prices, graph edges | porto_id |
| **`mark_profile`** | Porto convention | `domestic`, `registered_international` | **layout output** | porto_id |
| **`mark_type`** | Porto enum | `stamp`, `label` | product + marks profile | — |
| **`tracking_mode`** | Porto enum | `none`, `optional`, `included` | product row | — |
| **`envelope_id`** | Shared formats | `DL`, `C6`, `C4` | products, layouts | — |
| **`PortoMark.id`** | SDK runtime | `deutschepost:abc-123` | execution result | porto-data |
| **`features[].id`** | Provider | `tracking_number` row | services link | cross-provider |

Product and service `porto_id` enums are **disjoint** — products are size buckets only; `registered` is a **service** add-on (e.g. DE Einschreiben, UA intl registered surcharge).

---

## Same word, different layer (common traps)

```text
"registered" (service porto_id)
  └─ porto_id on SERVICE row     → Einschreiben / intl registered surcharge (SDK input)

"registered" (mark_profile id)
  └─ mark_profile in marks.json  → domestic registered STAMP size (layout output)

La Poste recommandée
  └─ products.porto_id: small    → full registered-letter SKU; pick native id (R1/R2/R3)

"domestic"
  ├─ zone id                     → destination lane in prices/graph
  └─ mark_profile id             → stamp footprint variant in marks.json

"id"
  ├─ products.id / services.id   → provider-native (standardbrief)
  ├─ marks.profiles[].id         → mark_profile (domestic)
  └─ PortoMark.id                → runtime execution handle
```

---

## File → key relations

```text
providers.json
  providers[deutschepost].country ──► policy/markets.json markets[DE]

products.json
  id ─────────────────────────────► graph.edges.products[id]
  id ─────────────────────────────► prices/products.json product_id
  porto_id ◄────────────────────── SDK letterType / porto_id input
  zones[] ────────────────────────► zones.json (subset)
  weight_tier? (optional) ──────► hint only (Deutsche Post); resolve weight via weights.json + graph
  envelope_ids[] ─────────────────► formats/envelopes.json
  mark_type ──────────────────────► marks.profiles[].mark_type (must match)
  delivery[] (zones, span, days) ─► operator SLA per zone group
  delivery[].weekdays? ───────────► override of markets[CC].working_days.weekdays
  included_features[] ────────────► features.json (bundled capabilities, not services)
  indemnity { tier, max.amount } ─► operator tier cap; currency from markets[CC]

policy/markets.json
  markets[CC].working_days ───────► default postal calendar for delivery hints

graph.json
  strategy ───────────────────────► resolution strategy (`service`, `id`, `speed`, `min`)
  edges.products[product_id].zones[] ──► zones used for that product
  edges.products[product_id].weight_tiers[] ► tiers allowed
  edges.marks[zone].profile ────────────► default mark profile id
  edges.marks[zone].services[id] ───────► profile override when service selected
  edges.wire[integration][product][zone].base ► adapter catalog code (purchase)
  edges.wire[integration][product][zone].services[id] ► service-composed code (DE Internetmarke)
  services[] (native service ids) ► services.json id list

services.json
  id ─────────────────────────────► prices/services.json service_id
  id ─────────────────────────────► graph.services[]
  porto_id ◄────────────────────── cross-operator service input
  integrations.* ─────────────────► online purchase supported (boolean; address rules live in SDK/Licko)
  features[] ─────────────────────► features.json

marks.json
  profiles[].id = mark_profile
  profiles[].size ────────────────► layout width/height (mm)
  default_profile ────────────────► fallback when edges.marks omits a zone

formats/layouts.json
  jurisdictions[DE].post_mark ────► envelope anchor (mm), not stamp size
```

---

## Resolution sequence (variable flow)

```text
INPUT                          RESOLVE TO NATIVE              OUTPUT FIELD
─────                          ─────────────────              ────────────
provider: deutschepost    →    (loader scope)
country_code: US          →    zone: world
weight_g: 20              →    weight_tier: W0020
letterType: small         →    porto_id: small
                          →    product.id: standardbrief      ResolvedData.product
                          →    base_price from prices         ResolvedData.pricing

services: [registered]    →    porto_id: registered
                          →    service.id: einschreiben

zone + services           →    graph.edges.marks[zone] + services overrides
                          →    mark_profile: registered_international
                          →    size 57×30, mark_type stamp

adapter purchase          →    graph.edges.wire.internetmarke[product][zone][service?]
                          →    wire_code (e.g. 10001) + API payload
                          →    PDF bytes                      PortoMark.content
                          →    tracking ref                   PortoMark.tracking_number
```

---

## Provider scope (four operators)

| `provider` | `country` | Primary `mark_type` | `mark_profile` rows today |
|------------|-----------|---------------------|---------------------------|
| `deutschepost` | DE | stamp | 4 (domestic … registered_international) |
| `laposte` | FR | label | 2 (domestic, international) |
| `swisspost` | CH | stamp | 2 |
| `ukrposhta` | UA | label | 1 (`domestic`; `world` zone maps to same profile via `graph.edges.marks`) — **letters only**; products `small` + domestic `large` (`dokument`) |

Folder rule: **`providers.json` key = `providers/<key>/` directory = SDK `provider` string.**

---

## Enum sources of truth

| Enum | Schema file |
|------|-------------|
| Product / service / feature `porto_id` | `schemas/porto_ids.schema.json` |
| `mark_type`, `tracking_mode` | `schemas/products.schema.json` |
| `mark_profile` ids | convention + per-provider `marks.json` (no global enum yet) |
| Provider keys | `providers.json` + directory names |
