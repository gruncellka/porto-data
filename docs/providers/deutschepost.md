# Deutsche Post — `porto_data/providers/deutschepost/`

Reference for **reconciling JSON with official letter/postcard tariffs** (not a legal tariff publication). Verify on [deutschepost.de](https://www.deutschepost.de) and current **Preisblätter** before production changes.

**Related:** [laposte.md](laposte.md) · [swisspost.md](swisspost.md)

---

## Files in this provider (and shared deps)

| Path | `file_type` | Role |
|------|-------------|------|
| `products.json` | `products` | Product ids, zones, weights, envelope refs, services |
| `prices/products.json` | `product_prices` | Base postage grid (product × zone × weight tier) |
| `prices/services.json` | `service_prices` | Surcharges (Einschreiben, etc.) |
| `services.json` | `services` | Service definitions |
| `features.json` | `features` | Feature ids used by services |
| `marks.json` | `marks` | Mark/label profiles |
| `weights.json` | `weights` | Weight tier ids (`W0020` …) |
| `zones.json` | `zones` | Domestic / EU / Europe / world buckets |
| `limits.json` | `limits` | Provider operational overlays on top of global policy (often empty) |
| `graph.json` | `graph` | Edges, units (EUR cents), `lookup_rules`, `available_services` |

**Loaded with the bundle (not under this folder):** `policy/jurisdictions.json`, `policy/restrictions.json`, `mails/envelopes.json`, `mails/layouts.json` — see `graph.json` `dependencies`.

---

## Pricing & geography rules (how we model)

- **Domestic:** prices by **format + weight** (no domestic “zone”).
- **International (standard letter ladder):** consumer pages use **“Alle Länder – ein Preis – weltweit”** — do **not** invent EU vs world splits unless a **current** Preisblatt says so. In data, **`zone_1_eu`**, **`zone_2_europe`**, **`world`** share the **same** international cent amounts per product/weight.
- **Add-ons:** Einschreiben etc. are **surcharges** on base postage; amounts in `prices/services.json`.
- **Out of scope in catalog:** **Warensendung** and other non–letter products from Internetmarke are **not** in `products.json` until explicitly added.

## Service support (proof/signature/AR)
- **Proof of mailing:** Internetmarke + Einschreiben generates an **Einlieferungsbeleg** (posting receipt) once scanned.
- **Recipient signature:** `einschreiben` variants require signature; `einschreiben_einwurf` does **not** (delivered to mailbox with tracking only).
- **Return receipt:** `einschreiben_rueckschein` available (return receipt/AR) as surcharge; stays in `service_prices.json`.

---

## Official sources (checklist)

| Date (UTC) | Source | Use |
|------------|--------|-----|
| 2026-03-23 | [Internetmarke](https://www.deutschepost.de/de/i/internetmarke-porto-drucken.html) | Product scope, shop links |
| 2026-03-23 | [Brief International](https://www.deutschepost.de/de/b/briefe-ins-ausland/brief-postkarte-international.html) | Worldwide single-price ladder |
| — | PDF [Gesamtpreisliste](https://www.deutschepost.de) (search site for current `dp-leistungen-und-preise-*.pdf`) | Authoritative ladders, **effective_from** |
| — | PDF `dp-preise-brief-international-*.pdf` | International letter rows |

---

## Official snapshots (€ — verify PDF)

**Domestic:** Postkarte / Standardbrief **0,95** · Kompakt **1,10** · Groß **1,80** · Maxi **2,90** (weights per site).

**International:** Postkarte/Standard **1,25** · Kompakt **1,80** · Groß **3,30** · Maxi **6,50** · heavy Maxi **17,00** (1,001–2,000 g, rules on site).

**Einschreiben (examples, add to base):** Einwurf **+2,35** · standard **+2,65** · Rückschein **+4,85** €.

---

## In-repo alignment (`effective_from`: `2026-01-01`, amounts in **cents**)

| `product_id` | Domestic | International (`zone_1_eu`, `zone_2_europe`, `world`) | Notes |
|--------------|---------:|--------------------------------------------------------:|-------|
| `postkarte` | 95 | 125 | Same € as Standard; **W0020**; envelope **C6** as postcard stand-in — verify DP format rules |
| `standardbrief` | 95 | 125 | W0020 |
| `kompaktbrief` | 110 | 180 | W0050 |
| `grossbrief` | 180 | 330 | W0500 |
| `maxibrief` | 290 | 650 | W1000 |
| `maxibrief_international_heavy` | — | 1700 | Abroad only, **W2000** (1,001–2,000 g) |

**`service_prices` (cents):** `einschreiben` 265 · `einschreiben_einwurf` 235 · `einschreiben_rueckschein` 485 · `zusatzversicherung` 250 — match surcharge rows on domestic tariff page.

**Graph:** every **weight tier** in the official ladder must have **edges**; `graph.json` `global_settings.price_lookup` documents the lookup contract.

---

## Reconcile

Download latest Preisblätter → diff `prices/*.json` and `graph.json` → `make validate`.
