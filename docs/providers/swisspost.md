# Swiss Post — `porto_data/providers/swisspost/`

Reference for **reconciling JSON with official letter tariffs** (not a legal tariff publication). Verify on [post.ch](https://www.post.ch) and brochure PDFs before production changes.

**Related:** [deutschepost.md](deutschepost.md) · [laposte.md](laposte.md)

---

## Files in this provider (and shared deps)

| Path | `file_type` | Role |
|------|-------------|------|
| `products.json` | `products` | **Explicit A vs B** domestic + international document products |
| `prices/products.json` | `product_prices` | Base postage (CHF → **rappen** in JSON) |
| `prices/services.json` | `service_prices` | Surcharges (e.g. thickness) |
| `services.json` | `services` | Service ids referenced by rules and prices |
| `features.json` | `features` | Features |
| `marks.json` | `marks` | Mark profiles |
| `weights.json` | `weights` | Tiers for standard / gross / maxi ladders |
| `zones.json` | `zones` | `domestic`, `zone_1_eu`, `world` |
| `limits.json` | `limits` | Provider overlays on global policy |
| **`rules.json`** | **`provider_rules`** | **Conditional rules** (e.g. thickness band → attach `brief_dicke_zuschlag`) — evaluated after base price resolution |
| `graph.json` | `graph` | Edges, units (CHF cents/rappen), `lookup_rules`, `available_services` |

**Loaded with the bundle:** `policy/jurisdictions.json`, `policy/restrictions.json`, `mails/envelopes.json`, `mails/layouts.json` — see `graph.json` `dependencies`.

**Swiss-only:** `rules.json` is not used for Deutsche Post / La Poste in this bundle.

---

## Pricing & geography rules (how we model)

- **Domestic:** two axes — **A Mail vs B Mail** (speed) and **standard vs gross** (format). Product ids must disambiguate (`a_post_*` vs `b_post_*`); resolver cannot infer from weight alone.
- **International documents:** **standard / gross / maxi** ladders from [international letters](https://www.post.ch/en/sending-letters/international-letters); in minimal data, **`zone_1_eu`** and **`world`** use the **same** cent amounts per row (matches destination-independent table where published).
- **`rules.json`:** e.g. domestic letter **thickness** in (20, 50] mm → attach service **`brief_dicke_zuschlag`** (amount in `prices/services.json`) — see `rules.json` and `graph.json` `global_settings.available_services`.
- **Not in minimal JSON:** Registered, A Mail Plus, international small goods, Pro Juventute — add when integrating those flows.

## Service support (proof/signature/AR)
- **Proof of mailing:** Registered (Einschreiben) creates a posting record/track event when accepted.
- **Recipient signature:** Registered requires signature on delivery.
- **Return receipt:** `Rückschein / avis de réception` available for registered; modeled as surcharge in `service_prices.json` when added.

---

## Official sources (checklist)

| Date (UTC) | Source | Use |
|------------|--------|-----|
| 2026-03-23 | [WebStamp info](https://www.post.ch/en/customer-center/online-services/webstamp/webstamp/info) | Scope of online franking |
| 2026-03-23 | [International letters](https://www.post.ch/en/sending-letters/international-letters) | CHF document letter tables |
| 2026-03-23 | [DigitalStamp](https://www.post.ch/en/sending-letters/franking-mail/franking/online-stamp-digitalstamp) | Domestic A/B CHF rows |
| — | [Versenden International (PDF)](https://www.post.ch/-/media/portal-opp/pm/dokumente/versenden-international-broschuere.pdf) | Dimensions, footnotes — refresh URL if post.ch moves the file |

---

## Official snapshots (CHF, VAT-exempt — verify site)

**Domestic (DigitalStamp-style)**

| Class | Standard 1–100 g | Gross 1–1000 g |
|-------|-----------------:|---------------:|
| **A Mail** | 1,20 | 2,50 |
| **B Mail** | 1,00 | 2,00 |

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

**Zones:** `zone_1_eu` and `world` — same amounts per `product_prices` row where the international table is flat.

**Rules:** `rules.json` → `domestic_letter_thickness` → `brief_dicke_zuschlag` (verify thickness band vs live tariff).

---

## Reconcile

Latest post.ch / PDF → diff `prices/*.json`, `rules.json`, `graph.json` → `make validate`.
