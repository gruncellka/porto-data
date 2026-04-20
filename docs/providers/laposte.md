# La Poste — `porto_data/providers/laposte/`

Reference for **reconciling JSON with official letter tariffs** (not a legal tariff publication). Verify on [laposte.fr](https://www.laposte.fr) and the **[catalogue intégral](https://www.laposte.fr/tarifs-postaux/catalogue-integral)** before production changes.

**Related:** [deutschepost.md](deutschepost.md) · [swisspost.md](swisspost.md)

---

## Files in this provider (and shared deps)

| Path | `file_type` | Role |
|------|-------------|------|
| `products.json` | `products` | Product ids (Lettre verte, suivie, Services Plus, recommandée, …) |
| `prices/products.json` | `product_prices` | Base postage grid |
| `prices/services.json` | `service_prices` | Optional services / AR lines |
| `services.json` | `services` | Service definitions |
| `features.json` | `features` | Features for services |
| `marks.json` | `marks` | Mark profiles |
| `weights.json` | `weights` | Tiers incl. **W0050** for recommandée steps |
| `zones.json` | `zones` | Domestic vs international groups |
| `limits.json` | `limits` | Provider overlays on global policy |
| `graph.json` | `graph` | Edges, units (EUR cents), lookups |

**Loaded with the bundle:** `policy/jurisdictions.json`, `policy/restrictions.json`, `mails/envelopes.json`, `mails/layouts.json` — see `graph.json` `dependencies`.

---

## Pricing & geography rules (how we model)

- **France + territories:** official tables footnote **métropolitaine, Monaco, Andorre, secteurs militaires, OM** — possible **complément aérien** OM above 100 g; encode per catalogue, don’t invent.
- **International:** separate prices per weight step from domestic; resolver must map **destination → domestic vs international** and the correct **zone** (EU / Europe / world from **`zones.json`**, refined via **catalogue intégral** if buckets are coarse).
- **Weight-first:** products and **`graph.json` edges** must match official **weight steps**; no impossible product × destination combinations.

## Service support (proof/signature/AR)
- **Proof of mailing:** online recommended label (vignette LR) provides electronic dépôt proof.
- **Recipient signature:** Lettre recommandée (R1/R2/R3, intl R1/R2) requires recipient signature.
- **Return receipt:** `avis de réception` (paper or digital) available as option on recommended; price rows belong in `service_prices.json`.

---

## Official sources (checklist)

| Date (UTC) | Source | Use |
|------------|--------|-----|
| 2026-03-23 | [Tarifs lettres 2026](https://www.laposte.fr/tarifs-postaux-courrier-lettres-timbres-2025) | Main tables (URL may still say 2025; content 2026) |
| 2026-03-23 | [Boutique MTEL tarifs](https://boutique.laposte.fr/mon-timbre-en-ligne/tarifs) | MTEL-aligned presentation |
| — | [Catalogue intégral](https://www.laposte.fr/tarifs-postaux/catalogue-integral) | Destination groups, edge cases, recommandée R1–R3 / R1–R2 |

---

## Official snapshots (€ — verify live pages)

**Lettre verte — France**

| ≤ weight | € |
|----------|---:|
| 20 g | 1,52 |
| 100 g | 3,10 |
| 250 g | 5,24 |
| 500 g | 7,41 |
| 1 kg | 9,29 |
| 2 kg | 11,14 |

**Lettre verte suivie — France vs international (examples)**

| ≤ weight | France | Intl. |
|----------|-------:|------:|
| 20 g | 2,02 | 5,05 |
| 100 g | 3,60 | 7,65 |
| 2 kg | 11,64 | 34,50 |

**Lettre Services Plus — France:** 20 g **3,47** … 2 kg **12,01** (full ladder on site).

**Lettre recommandée:** domestic **R1–R3** and international **R1–R2** — copy from live page or catalogue when encoding `prices/products.json`.

---

## In-repo alignment (`effective_from`: `2026-01-01`, amounts in **cents**)

| `product_id` | Domestic | International |
|--------------|----------|-----------------|
| `lettre_verte` | W0020…W2000 → **152, 310, 524, 741, 929, 1114** | — (France-only in data) |
| `lettre_verte_suivie` | **202, 360, 574, 791, 979, 1164** | **505, 765, 1445, 1940, 3450, 3450** on `zone_1_eu`, `zone_2_europe`, `world` (one column replicated — refine with catalogue if needed) |
| `lettre_services_plus` | **347, 457, 578, 810, 1035, 1201** | — |
| `lettre_recommandee_r_un` / `r_deux` / `r_trois` | R1–R3 table | — |
| `lettre_recommandee_inter_r_un` / `inter_r_deux` | — | R1–R2 × zones |

**Services (examples):** `suivi_option` 50 · `avis_de_reception_national` 145 · `avis_de_reception_international` 150 (per official recommandée lines).

---

## Reconcile

Latest catalogue / tariff pages → diff `prices/*.json`, `zones.json`, `graph.json` → `make validate`.
