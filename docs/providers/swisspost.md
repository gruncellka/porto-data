# Swiss Post — `porto_data/providers/swisspost/`

Reference for **reconciling JSON with official letter tariffs** (not a legal tariff publication). Verify on [post.ch](https://www.post.ch) and brochure PDFs before production changes.

---

## Verification status

| Field | Value |
|-------|--------|
| Last checked (UTC) | 2026-06-21 |
| Confidence | **verified** — A/B domestic standard + large letters, international document ladder, thickness surcharge |
| Baseline | A/B letter prices **unchanged 2026-01-01** per Swiss Post press release; JSON `effective_from`: **2026-01-01** |

---

## Files in this provider (and shared deps)

| Path | `file_type` | Role |
|------|-------------|------|
| `products.json` | `products` | **Explicit A vs B** domestic + international document products |
| `prices/products.json` | `product_prices` | Base postage (CHF → **rappen** in JSON) |
| `prices/services.json` | `service_prices` | Surcharges (thickness, A Mail Plus) |
| `services.json` | `services` | Service ids referenced by rules and prices |
| `features.json` | `features` | Features |
| `marks.json` | `marks` | Mark profiles |
| `weights.json` | `weights` | Tiers for standard / gross / maxi ladders |
| `zones.json` | `zones` | `domestic`, `zone_1_eu`, `world` |
| `limits.json` | `limits` | Provider overlays on global policy |
| **`rules.json`** | **`provider_rules`** | Thickness band → `brief_dicke_zuschlag` |
| `graph.json` | `graph` | Edges, units (CHF cents/rappen), `services` |

**Loaded with the bundle:** `policy/jurisdictions.json`, `policy/markets.json`, `policy/restrictions.json`, `formats/envelopes.json`, `formats/layouts.json` — see `graph.json` `dependencies`.

**Swiss-only:** `rules.json` is not used for Deutsche Post / La Poste in this bundle.

---

## Known pitfalls

- **A Mail vs B Mail:** separate product ids (`a_post_*` vs `b_post_*`); resolver cannot infer from weight alone.
- **Thickness surcharge:** domestic letters **>2 cm and ≤5 cm** → **+2,00 CHF** via `rules.json` + `brief_dicke_zuschlag` (200 rappen).
- **Midi letters (101–500 g):** separate prices on site (A 1,70 / B 1,40) — **not** split in minimal model (standard product covers 1–100 g flat rate per DigitalStamp table).
- **International flat zones:** `zone_1_eu` and `world` share amounts where post.ch table is destination-independent.

---

## Pricing & geography rules (how we model)

- **Domestic:** A vs B × standard vs gross (large) format products.
- **International documents:** standard / gross / maxi ladders from [international letters](https://www.post.ch/en/sending-letters/international-letters).
- **`rules.json`:** thickness (20, 50] mm → attach **`brief_dicke_zuschlag`**.

## Service support (proof/signature/AR)

- **Proof of mailing:** Registered flow (not in minimal JSON).
- **Recipient signature:** Registered requires signature when modeled.
- **Return receipt:** deferred until registered products added.

---

## Official sources (checklist)

| Date (UTC) | Source | Use |
|------------|--------|-----|
| 2026-06-21 | [DigitalStamp](https://www.post.ch/en/sending-letters/franking-mail/franking/online-stamp-digitalstamp) | Domestic A/B standard + large |
| 2026-06-21 | [Domestic letters](https://www.post.ch/en/sending-letters/domestic-letters) | Midi tiers, thickness footnote |
| 2026-06-21 | [International letters](https://www.post.ch/en/sending-letters/international-letters) | CHF document letter tables |
| 2026-06-21 | [Press release Offer 2026](https://www.post.ch/en/about-us/media/press-releases/2025/swiss-post-is-adjusting-prices-and-collection-times-in-selected-cases) | A/B letters unchanged Jan 2026 |
| — | [Versenden International (PDF)](https://www.post.ch/-/media/portal-opp/pm/dokumente/versenden-international-broschuere.pdf) | Dimensions, footnotes |

---

## Official snapshots (CHF — post.ch, 2026)

**Domestic (DigitalStamp — standard / large, 1–100 g / 1–1000 g)**

| Class | Standard 1–100 g | Large 1–1000 g |
|-------|-----------------:|---------------:|
| **A Mail** | 1,20 | 2,50 |
| **B Mail** | 1,00 | 2,00 |

**Thickness:** >2 cm up to 5 cm → **+2,00 CHF** surcharge.

**International — documents**

| Ladder | Weight steps (summary) | CHF |
|--------|-------------------------|-----|
| Standard | 20 / 50 / 100 g | 1,90 / 3,10 / 4,30 |
| Gross | 100 / 250 / 500 g | 4,30 / 7,50 / 12,00 |
| Maxi | 500 / 1000 / 2000 g | 13,00 / 19,00 / 26,00 |

---

## In-repo alignment (`effective_from`: `2026-01-01`, amounts in **rappen**)

| Domestic `product_id` | Standard W0020–W0100 | Gross W0250–W1000 |
|-----------------------|---------------------:|-------------------:|
| `a_post_standardbrief`, `a_post_grossbrief` | A **120** | A **250** |
| `b_post_standardbrief`, `b_post_grossbrief` | B **100** | B **200** |

| International `product_id` | Standard | Gross | Maxi |
|-----------------------------|----------|-------|------|
| `international_standardbrief` | W0020 **190**, W0050 **310**, W0100 **430** | — | — |
| `international_grossbrief` | — | W0250 **750**, W0500 **1200** | — |
| `international_maxibrief` | — | — | W0500 **1300**, W1000 **1900**, W2000 **2600** |

**`service_prices`:** `brief_dicke_zuschlag` **200** (CHF 2,00).

**Zones:** `zone_1_eu` and `world` — same amounts per row where table is flat.

**Rules:** `domestic_letter_thickness` → thickness (20, 50] mm → `brief_dicke_zuschlag`.

---

## Out of scope

- Domestic **midi** letter tier (101–500 g at 1,70 / 1,40 CHF)
- **Registered**, A Mail Plus (service price exists but no registered product flow)
- International small goods, Pro Juventute

---

## Reconcile

Latest post.ch / PDF → diff `prices/*.json`, `rules.json`, `graph.json` → update status date → `make validate` → `make metadata`.
