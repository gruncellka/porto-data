# La Poste — `porto_data/providers/laposte/`

Reference for **reconciling JSON with official letter tariffs** (not a legal tariff publication). Verify on [laposte.fr](https://www.laposte.fr) and the **[catalogue intégral](https://www.laposte.fr/tarifs-postaux/catalogue-integral)** before production changes.

**Related:** [deutschepost.md](deutschepost.md) · [ukrposhta.md](ukrposhta.md) · [swisspost.md](swisspost.md) · [tariff-verification.md](../tariff-verification.md)

---

## Verification status

| Field | Value |
|-------|--------|
| Last checked (UTC) | 2026-06-21 |
| Confidence | **verified** — Lettre verte / suivie / Services Plus ladders + recommandée products spot-checked vs laposte.fr 2026 |
| Baseline | `effective_from`: **2026-01-01** (tarifs from **2026-01-01** métropole) |

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
| `graph.json` | `graph` | Edges, units (EUR cents), `services` |

**Loaded with the bundle:** `policy/jurisdictions.json`, `policy/markets.json`, `policy/restrictions.json`, `formats/envelopes.json`, `formats/layouts.json` — see `graph.json` `dependencies`.

---

## Known pitfalls

- **Territories footnote:** métropole, Monaco, Andorre, secteurs militaires, OM — possible **complément aérien** OM above 100 g; encode per catalogue, don’t invent.
- **International zones:** separate prices per weight; map destination → zone via **`zones.json`** + catalogue intégral if buckets are coarse.
- **Recommandée as products:** R1–R3 / international R1–R2 are **products** with own price rows, not only services.
- **MTEL discount:** online stamp **3 ct** below counter price — bundle uses **official table** (counter) amounts unless MTEL product is added.

---

## Pricing & geography rules (how we model)

- **Weight-first:** products and **`graph.json` edges** must match official **weight steps**.
- **International:** `zone_1_eu`, `zone_2_europe`, `world` — replicate international column where catalogue uses one international bucket per product.

## Service support (proof/signature/AR)

- **Proof of mailing:** recommended label (vignette LR) → electronic dépôt proof.
- **Recipient signature:** Lettre recommandée requires signature.
- **Return receipt:** `avis de réception` in `service_prices.json`.

---

## Official sources (checklist)

| Date (UTC) | Source | Use |
|------------|--------|-----|
| 2026-06-21 | [Tarif lettre verte 2026](https://www.laposte.fr/tarif-lettre-verte) | Lettre verte ladder |
| 2026-06-21 | [Tarifs postaux 2026](https://www.laposte.fr/tarifs-postaux-courrier-lettres-timbres-2026) | All letter products |
| 2026-06-21 | [Boutique MTEL tarifs](https://boutique.laposte.fr/mon-timbre-en-ligne/tarifs) | Online franking presentation |
| — | [Catalogue intégral](https://www.laposte.fr/tarifs-postaux/catalogue-integral) | Destination groups, recommandée R1–R3 / R1–R2 |

---

## Official snapshots (€ — laposte.fr 2026)

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

**Lettre recommandée:** domestic **R1–R3** and international **R1–R2** — see live page / catalogue for full matrix.

---

## In-repo alignment (`effective_from`: `2026-01-01`, amounts in **cents**)

| `product_id` | Domestic | International |
|--------------|----------|-----------------|
| `lettre_verte` | W0020…W2000 → **152, 310, 524, 741, 929, 1114** | — (France-only in data) |
| `lettre_verte_suivie` | **202, 360, 574, 791, 979, 1164** | **505, 765, …, 3450** on `zone_1_eu`, `zone_2_europe`, `world` |
| `lettre_services_plus` | **347, 457, 578, 810, 1035, 1201** | — |
| `lettre_recommandee_r_un` / `r_deux` / `r_trois` | R1–R3 table | — |
| `lettre_recommandee_inter_r_un` / `inter_r_deux` | — | R1–R2 × zones |

**Services (examples):** `suivi_option` 50 · `avis_de_reception_national` 145 · `avis_de_reception_international` 150.

---

## Out of scope

- MTEL-only −0,03 € online discount as separate price rows
- OM air complement modeling unless explicitly added per catalogue
- Non-letter products (colis, etc.)

---

## Reconcile

Latest catalogue / [tarifs 2026](https://www.laposte.fr/tarifs-postaux-courrier-lettres-timbres-2026) → diff `prices/*.json`, `zones.json`, `graph.json` → update status date → `make validate` → `make metadata`.
