# Identity map — names, ids, variables, relations

One-page map of **who names what** across **porto-data** (JSON + schemas) and **carrier APIs**. Consumers (Porto SDK, apps) load this bundle; this repo has **no resolver and no SDK surface**.

**See also:** [id.md](id.md) · [marks.md](marks.md) · [resolution.md](resolution.md)

---

## Layer stack

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│  CONSUMER (SDK / app)                                                        │
│  input:  porto_id, country_code, weight, service porto_ids                  │
│  output: resolved product/price facts (+ mark bytes after adapter call)     │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │ reads bundle only via loader
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

Do **not** document consumer SDK class or method names here — that drifts with SDK releases. Catalog contracts stay in this file; SDK API lives in Lab / SDK repos.

---

## Identifier cheat sheet

| Name | Owner | Example | Used in | Never used in |
|------|-------|---------|---------|---------------|
| **`provider`** | Porto registry + **`providers/<id>/` path** | `deutschepost` | consumer context, bundle layout | in-file repeat on path-scoped JSON |
| **`label` / `name`** | Display / legal | `"Deutsche Post"`, `"Deutsche Post AG"` | UI, docs | resolution |
| **`country`** | Registry → markets | `DE`, `FR`, `UA`, `CH` | VAT, currency, layouts | product id |
| **`porto_id`** (product) | Porto enum | `small`, `medium`, `large`, `extra_large` | **consumer input** | graph, prices |
| **`porto_id`** (service) | Porto enum | `registered`, `insurance` | **consumer input** | graph.services list |
| **`porto_id`** (feature) | Porto enum | `tracking` | semantics | prices |
| **`id`** (product/service) | Provider native | `standardbrief`, `einschreiben` | **graph, prices, rules** | consumer input |
| **`wire_code`** | Graph wire edge | `10001`, `"letter"` | **adapter API only** | products/services rows |
| **`zone`** | Provider | `domestic`, `world`, `zone_1_eu` | prices, graph edges | porto_id |
| **`weight_tier`** | Provider | `W0020`, `W1000` | prices, graph edges | porto_id |
| **`mark_profile`** | Porto convention | `domestic`, `registered_international` | **layout output** | porto_id |
| **`mark_type`** | Porto enum | `stamp`, `label` | product + marks profile | — |
| **`tracking`** | Porto enum | `none`, `optional`, `included` | product row | — |
| **`envelope_id`** | Shared formats | `DL`, `C6`, `C4` | products, layouts | — |
| **`wire`** | `execution.json` | `internetmarke` | execution manifest | graph body |
| **`billing[]` / `execution[]`** | `execution.json` | `wallet`, `mark` | capability tokens | graph body |
| **`graph.strategy`** | Provider graph | `service`, `id`, `speed`, `min` | **Disambiguation policy** when multiple products share a `porto_id` | hard-coded provider rules in consumers |
| **`features[].id`** | Provider | `sendungsnummer` | services link | cross-provider |

Product and service `porto_id` enums are **disjoint** — products are size buckets only; `registered` is a **service** add-on (e.g. DE Einschreiben, UA intl registered surcharge).

---

## Same word, different layer (common traps)

```text
"registered" (service porto_id)
  └─ porto_id on SERVICE row     → Einschreiben / intl registered surcharge (consumer input)

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
  └─ mark result id (consumer)   → UUID after purchase — not a provider handle

"tracking"
  ├─ products.tracking            → none | optional | included
  ├─ service porto_id             → priced add-on (option suivi, A-Mail Plus)
  ├─ feature porto_id             → capability (native id still sendungsnummer / numero_suivi)
  └─ Internetmarke mark / shop id → runtime mark handle; basic scan/status only
                                    NOT the tracking service; does not make DE products `included`
```

Deutsche Post letters stay `products.tracking: optional`. Buying the stamp yields a mark number the host may use for basic IM status; **Sendungsverfolgung / Sendungsnummer** is the Einschreiben feature `tracking`. Do not catalog IM shop-id as feature `tracking`. Do not set DE `tracking: included` because a stamp has a number.

---

## File → key relations

```text
providers.json
  providers[deutschepost].country ──► policy/markets.json markets[DE]

products.json
  id ─────────────────────────────► graph.edges.products[id]
  id ─────────────────────────────► prices/products.json product_id
  porto_id ◄────────────────────── consumer porto_id input
  zones[] ────────────────────────► zones.json (subset)
  weight_tier? (optional) ──────► hint only (Deutsche Post); resolve weight via weights.json + graph
  envelope_ids[] ─────────────────► formats/envelopes.json
  mark_type ──────────────────────► marks.profiles[].mark_type (must match)
  delivery[] (zones, span, days) ─► operator SLA per zone group
  delivery[].weekdays? ───────────► override of markets[CC].working_days.weekdays
  tracking ───────────────────────► none | optional | included (not service/feature porto_id)
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
  edges.wire[wire][product][zone].base ► adapter catalog code (purchase)
  edges.wire[wire][product][zone].services[id] ► service-composed code (DE Internetmarke)
  services[] (native service ids) ► services.json id list

services.json
  id ─────────────────────────────► prices/services.json service_id
  id ─────────────────────────────► graph.services[]
  porto_id ◄────────────────────── cross-operator service input
  features[] ─────────────────────► features.json id or porto_id; tracking iff feature porto_id is tracking

marks.json
  profiles[].id = mark_profile
  profiles[].size ────────────────► layout width/height (mm)
  default_profile ────────────────► fallback when edges.marks omits a zone

execution.json
  wire ───────────────────────────► must match graph.edges.wire key (e.g. internetmarke)
  billing[] / execution[] ─────────► capability tokens (wallet, mark)
  graph.dependencies.execution ► bundle index only — not execution data

formats/layouts.json
  jurisdictions[DE].post_mark ────► envelope anchor (mm), not stamp size

formats/addresses.json
  jurisdictions[DE].standard ─────► must match layouts standard when layouts[CC] exists
  jurisdictions[DE].forms[] ──────► street / post_box required fields (not compose geometry)
```

---

## Resolution sequence (variable flow)

```text
INPUT                          RESOLVE TO NATIVE              OUTPUT FIELD
─────                          ─────────────────              ────────────
provider: deutschepost    →    (loader scope)
country_code: US          →    zone: world
weight: 20               →    weight_tier: W0020
porto_id: small           →    porto_id: small
                          →    product.id: standardbrief      product
                          →    base_price from prices         pricing

services: [registered]    →    porto_id: registered
                          →    service.id: einschreiben

zone + services           →    graph.edges.marks[zone] + services overrides
                          →    mark_profile: registered_international
                          →    size 57×30, mark_type stamp

adapter purchase          →    graph.edges.wire.internetmarke[product][zone][service?]
                          →    wire_code (e.g. 10001) + API payload
                          →    execution.json.wire selects wire table
                          →    execution.json billing/execution gate capabilities
                          →    PDF/PNG bytes                      mark content
                          →    carrier tracking ref          (runtime string; not a porto_id)
```

---

## Provider scope (four operators)

| `provider` | `country` | Primary `mark_type` | `mark_profile` rows today |
|------------|-----------|---------------------|---------------------------|
| `deutschepost` | DE | stamp | 4 (domestic … registered_international) |
| `laposte` | FR | label | 2 (domestic, international) |
| `swisspost` | CH | stamp | 2 |
| `ukrposhta` | UA | label | 1 (`domestic`; `world` zone maps to same profile via `graph.edges.marks`) — **letters only**; products `small` + domestic `large` (`dokument`) |

Folder rule: **`providers.json` key = `providers/<key>/` directory = consumer `provider` string.**

---

## Enum sources of truth

| Enum | Schema file |
|------|-------------|
| Product / service / feature `porto_id` | `schemas/porto_ids.schema.json` |
| `mark_type`, `tracking` | `schemas/products.schema.json` |
| `mark_profile` ids | convention + per-provider `marks.json` (no global enum yet) |
| Provider keys | `providers.json` + directory names |
