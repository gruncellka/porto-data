# Identity map — names, ids, variables, relations

One-page map of **who names what** across **porto-data** (JSON + schemas) and **carrier APIs**. Consumers (Porto SDK, apps) load this bundle; this repo has **no resolver and no SDK surface**.

**See also:** [id.md](id.md) · [marks.md](marks.md) · [resolution.md](resolution.md)

---

## Layer stack

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│  CONSUMER (SDK / app)                                                        │
│  input:  country_code, weight, envelope?, service kind or id                │
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
| **`id`** (product/service/feature) | Porto catalog | `standardbrief`, `einschreiben` | **graph, prices, rules, pins** | — |
| **`name`** | Provider original | `Standardbrief`, `Einschreiben` | display | resolution key |
| **`label`** | Porto English | `Standard Letter` | UI, docs | resolution key |
| **`kind`** (service/feature) | Porto enum | `registered`, `tracking` | **cross-provider intent** | graph, prices |
| **`wire_code`** | Graph wire edge | `10001`, `"letter"` | **adapter API only** | products/services rows |
| **`zone`** | Provider | `domestic`, `world`, `zone_1_eu` | prices, graph edges | product id |
| **`weight_tier`** | Provider | `W0020`, `W1000` | prices, graph edges | product id |
| **`mark_profile`** | Porto convention | `domestic`, `registered_international` | **layout output** | product id |
| **`mark_type`** | Porto enum | `stamp`, `label` | product row | — |
| **`type`** (marks profile) | Porto enum | `stamp`, `label` | `marks.profiles[]` (must match product `mark_type`) | not address |
| **`requires`** | Porto tokens | `ADDRESS_SENDER`, `ADDRESS_RECIPIENT` | product / service / feature / mark profile | omit when none |
| **`tracking`** | Porto enum | `none`, `optional`, `included` | product row | — |
| **`envelope_id`** | Shared formats | `DL`, `C6`, `C4` | products, layouts | — |
| **`wire`** | `execution.json` | `internetmarke` | execution manifest | graph body |
| **`billing[]` / `execution[]`** | `execution.json` | `wallet`, `mark` | capability tokens | graph body |
| **`graph.strategy`** | Provider graph | `service`, `id`, `speed`, `min` | **Disambiguation** when multiple products share zone+weight | hard-coded provider rules in consumers |
| **`features[].id`** | Provider | `sendungsnummer` | services link | cross-provider |

Product rows have **no `kind`**. Service/feature `kind` enums may share tokens (`tracking`) where a priced add-on and a capability align.

---

## Same word, different layer (common traps)

```text
"registered" (service kind)
  └─ kind on SERVICE row           → Einschreiben / intl registered surcharge (consumer intent)

"registered" (mark_profile id)
  └─ mark_profile in marks.json    → domestic registered STAMP size (layout output)

La Poste recommandée
  └─ products.id (e.g. lettre_recommandee_r_un) → full registered-letter SKU; pick native id (R1/R2/R3)

"domestic"
  ├─ zone id                       → destination lane in prices/graph
  └─ mark_profile id               → stamp footprint variant in marks.json

"id"
  ├─ products.id / services.id     → provider-native (standardbrief)
  ├─ marks.profiles[].id           → mark_profile (domestic)
  └─ mark result id (consumer)     → UUID after purchase — not a provider handle

"tracking"
  ├─ products.tracking             → none | optional | included
  ├─ service kind                  → priced add-on (option suivi, A-Mail Plus)
  ├─ feature kind                  → capability (native id still sendungsnummer / numero_suivi)
  └─ Internetmarke mark / shop id  → runtime mark handle; basic scan/status only
                                     NOT the tracking service; does not make DE products `included`
```

Deutsche Post letters stay `products.tracking: optional`. Buying the stamp yields a mark number the host may use for basic IM status; **Sendungsverfolgung / Sendungsnummer** is the Einschreiben feature `kind: tracking`. Do not catalog IM shop-id as feature `kind: tracking`. Do not set DE `tracking: included` because a stamp has a number.

---

## File → key relations

```text
providers.json
  providers[deutschepost].country ──► policy/markets.json markets[DE]

products.json
  id ─────────────────────────────► graph.edges.products[id]
  id ─────────────────────────────► prices/products.json product_id
  zones[] ────────────────────────► zones.json (subset)
  weight_tier? (optional) ──────► hint only (Deutsche Post); resolve weight via weights.json + graph
  envelope_ids[] ─────────────────► formats/envelopes.json
  mark_type ──────────────────────► marks.profiles[].type (must match)
  delivery[] (zones, span, days) ─► operator SLA per zone group
  delivery[].weekdays? ───────────► override of markets[CC].working_days.weekdays
  tracking ───────────────────────► none | optional | included (product posture; not service/feature kind)
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
  kind ◄────────────────────────── cross-operator service intent
  features[] ─────────────────────► features.json id only; tracking iff linked feature kind is tracking

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
envelope: DL             →    filter envelope_ids[]
                          →    product.id: standardbrief      product
                          →    base_price from prices         pricing

services: [registered]    →    kind: registered
                          →    service.id: einschreiben

zone + services           →    graph.edges.marks[zone] + services overrides
                          →    mark_profile: registered_international
                          →    size 57×30, type stamp

adapter purchase          →    graph.edges.wire.internetmarke[product][zone][service?]
                          →    wire_code (e.g. 10001) + API payload
                          →    execution.json.wire selects wire table
                          →    execution.json billing/execution gate capabilities
                          →    PDF/PNG bytes                      mark content
                          →    carrier tracking ref          (runtime string; not catalog id)
```

---

## Provider scope (four operators)

| `provider` | `country` | Primary `mark_type` | `mark_profile` rows today |
|------------|-----------|---------------------|---------------------------|
| `deutschepost` | DE | stamp | 4 (domestic … registered_international) |
| `laposte` | FR | label | 2 (domestic, international) |
| `swisspost` | CH | stamp | 2 |
| `ukrposhta` | UA | label | 1 (`domestic`; `world` zone maps to same profile via `graph.edges.marks`) — **letters only**; products `lyst_standartnyi` + domestic `dokument` |

Folder rule: **`providers.json` key = `providers/<key>/` directory = consumer `provider` string.**

---

## Enum sources of truth

| Enum | Schema file |
|------|-------------|
| Service / feature `kind` | `schemas/kinds.schema.json` |
| `mark_type`, `tracking` | `schemas/products.schema.json` |
| `mark_profile` ids | convention + per-provider `marks.json` (no global enum yet) |
| Provider keys | `providers.json` + directory names |
