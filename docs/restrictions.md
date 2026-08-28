# Restrictions concern matrix

Research / provenance scaffold for destination restrictions on the ordinary-letter / postal surface. Explains why certain destinations appear in, or stay out of, shipped [`porto_data/policy/restrictions.json`](../porto_data/policy/restrictions.json).

**Not a catalog.** Not permission to change `restrictions.json` automatically. Catalog shape and conventions: [policy.md](policy.md).

Research date: **2026-08-27** (operator pass + legal / regulatory verify). **Result** prefers facts that survive legal / regulatory verification for *letter-mail*, not goods-only embargo lists alone.

## Evidence boundary

This document records research findings, source observations, and classification decisions for Porto Data. It is not a statement of political status, recognition, legal advice, or current universal postal availability.

Absence from an operator restriction list does not establish availability.

Operator restrictions are attributed to the operator unless an independent legal or regulatory source establishes a broader rule.

Sanctions, territorial status, conflict, or recognition issues are included only when investigated for a possible postal consequence. Their existence alone does not constitute a Porto restriction.

## Purpose

The inventory under `restrictions.json` covered a smaller emit set; some historical rows were weak or not postal-specific. This matrix is a research pass: **30 concern destinations × 4 operators**, then a **legal / regulatory** check for unclear or split rows.

Tiny territories (BV, HM, PN, …) stay out unless operator research surfaces them on the product surface.

## Method

1. Record an **operator fact per destination** (Deutsche Post, Swiss Post, La Poste, Ukrposhta).
2. Do **not** collapse the four operators into one verdict early.
3. For unclear / split rows, verify at **national competent authority** and **legal / regulatory** level (EU, UN, and other frameworks as relevant): is there a rule that interrupts *postal correspondence*, or only goods / dual-use / person listings?
4. Then classify:

```text
same operator rule across origins?
  → provider-independent destination restriction candidate

depends on provider jurisdiction / legal framework?
  → legal/framework restriction

special destination handling (not a stop)?
  → routing restriction

no letter-mail ban found in cited legal sources; only some operators refuse?
  → provider-specific (not a global Restrictions legal row)

no postal fact; recognition / postage / service options only?
  → other-domain | remove | unresolved
```

## How to fill cells

| Column | Meaning |
| --- | --- |
| Destination | ISO 3166-1 alpha-2 (+ short label) |
| Geography | `country` or `regions` (prefer **source wording** for territorial labels; do not unify legal vocabularies) |
| Operator columns | Short postal fact + source tag |
| Legal / regulatory evidence | Letter-mail relevant law or regulation (not “sanctions exist somewhere”) |
| Durable? | `yes` / `no` / `candidate` / `unclear` — `yes` only when durability is evidenced beyond a single multi-operator snapshot |
| Result | Candidate home after operator **and** legal / regulatory check |

### Operator cell conventions

| Phrase | Means |
| --- | --- |
| **ordinary** | No country-level stop found in the cited operator source for ordinary letter mail. **Not** confirmation that delivery succeeds. |
| **not on FR-sus** / **not on UA-nd** / **no XX entry** | Absence of evidence in that source — **not** positive evidence of availability. |
| **stop** / **suspended** / **no acceptance** | Cited operator refuses or suspends acceptance for the stated class (docs / goods / service). |
| **no letter-mail ban found** | In the cited legal / regulatory sources, no correspondence prohibition was identified. Does **not** assert absolute absence of every possible rule. |

## Sources

| Tag | Source |
| --- | --- |
| DP-04 | Deutsche Post *Länderinformationen* **04/2026** ([PDF](https://www.deutschepost.de/dam/jcr:245118f2-d254-4406-bc74-1d50e3aa8d0b/dp-brief-international-landfuerland-012026.pdf)) |
| DP-07 | Deutsche Post *Wichtige Hinweise* ([page](https://www.deutschepost.de/de/b/briefe-ins-ausland/laenderinformationen.html)), **2026-07-28** snapshot |
| CY-faq | [Cyprus Post receiving FAQ](https://www.cypruspost.post/en/faq-receive-items) |
| CH-tr | Swiss Post *Transit restrictions* ([Verkehrseinschränkungen](https://service.post.ch/vgkklp/info/informationen/Verkehrseinschraenkungen?lang=en)), **2026-08-27** |
| FR-sus | La Poste suspended destinations ([aide](https://aide.laposte.fr/professionnel/contenu/quelles-sont-les-destinations-internationales-suspendues-et-pourquoi); [machines](https://www.laposte.fr/entreprise-collectivites/actualites/machines-affranchir) **2026-08-03**) |
| UA-nd | Ukrposhta no-delivery list, status **12.05.2026** ([Export School](https://e-export.ukrposhta.ua/spysok-krayin-v-yaki-ne-zdijsnyuyetsya-dostavka-stanom-na-15-08-2025/)) |
| UA-me | Ukrposhta Mid-East reopen ([Export School](https://e-export.ukrposhta.ua/5926/)) |
| EU-RU | Consilium sanctions Q&A: road-transport ban **does not affect mail services** ([consilium](https://www.consilium.europa.eu/en/policies/sanctions-against-russia-explained/)) |
| OHCHR-PN | UN Special Procedures letter **AL OTH 74/2022**: no EU-imposed ban on postal services to RU/BY; operator suspension can be over-compliance ([OHCHR](https://spcommreports.ohchr.org/TMResultsBase/DownLoadFile?gId=37220)) |
| EU-KP | Council Regulation (EU) **2017/1509** (DPRK): trade / dual-use / luxury / cargo inspection — not a correspondence stop ([EUR-Lex](https://eur-lex.europa.eu/eli/reg/2017/1509/oj)) |
| BAFA-KP | [BAFA Nordkorea](https://www.bafa.de/DE/Aussenwirtschaft/Ausfuhrkontrolle/Embargos/Nordkorea/nordkorea_node.html) — DE implementation of EU/UN goods & finance measures |
| SECO-KP | [SECO Nordkorea](https://www.seco.admin.ch/de/massnahmen-gegenueber-nordkorea) — CH ordinance; cargo controls, not letter ban |
| EU-SY | Council Regulation (EU) **36/2012** and later amendments (incl. **2025** easing, e.g. 2025/1098): goods / repression / arms — not identified as a letter-mail stop |
| EU-HTI | Council Regulation (EU) **2022/2309** / Decision (CFSP) **2022/2319** (Haiti): arms / listed persons & entities — **no letter-mail ban found** |
| EU-YEM | EU restrictive measures in view of the situation in Yemen (targeted persons/entities; arms-related) — **no letter-mail ban found** |
| EU-SDN | EU / UN Sudan restrictive measures (targeted persons/entities; selected goods where applicable) — **no letter-mail ban found** |
| EU-AFG | EU measures aligned with **UN Security Council resolution 1988 (2011)** sanctions regime (targeted persons/entities; arms-related) — **no letter-mail ban found** |
| EU-UA | EUR-Lex **692/2014** (Crimea/Sevastopol); **2022/263** / **2022/1903** (non-government-controlled areas of Donetsk, Luhansk, Kherson, Zaporizhzhia); SECO Ukraine measures; UA law on **temporarily occupied territories** ([zakon](https://zakon.rada.gov.ua/laws/show/1207-18)) |

Abbreviations: **docs** = documents / letter mail; **goods** = merchandise; **stop** = no acceptance in the cited operator source.

## Matrix

| Destination | Geography | Deutsche Post | Swiss Post | La Poste | Ukrposhta | Legal / regulatory evidence | Durable? | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AF Afghanistan | country | ordinary DP-04 | URGENT no (docs ban not stated) CH-tr | suspended FR-sus | no acceptance UA-nd | EU-AFG / UN 1988 regime = targeted persons & listed goods — **no letter-mail ban found** | no | provider-specific |
| BH Bahrain | country | temp 07-28; ordinary DP-04 | lithium goods only CH-tr | not on FR-sus | reopen 04.05.2026 UA-me | no EU/UN postal correspondence block identified | no | remove |
| BY Belarus | country | ordinary DP-04 | URGENT no; lithium goods CH-tr | goods suspended; **docs OK** FR-sus | no acceptance UA-nd | EU Belarus sanctions; **mail services not banned** EU-RU / OHCHR-PN | no | provider-specific (Ukrposhta acceptance; not EU letter ban) |
| CF Central African Republic | country | ordinary DP-04 | URGENT no CH-tr | not on FR-sus | not on UA-nd | UN arms embargo — **no letter-mail ban found** | no | remove |
| CU Cuba | country | ordinary DP-04; 07-28 capacity DP-07 | **docs+goods suspended** CH-tr | not on FR-sus | not on UA-nd | no EU letter-mail ban found; US OFAC is out of scope for DE/FR/CH/UA origins | no | provider-specific (CH transport) |
| CY Cyprus | regions — northern Cyprus (destination-side) | ordinary; **routing** CY-faq | no CY stop CH-tr | not on FR-sus | not on UA-nd | no EU/UN correspondence stop identified; destination-side handling | yes | routing |
| EH Western Sahara | country | recognition / postage essay | URGENT + PostPac no CH-tr | not on FR-sus | not on UA-nd | status / postage — **not** identified as inbound letter stop | no | other-domain |
| GE Georgia | regions — Abkhazia / South Ossetia | postage / sector jurisdiction | no GE stop CH-tr | delays; not suspended FR-sus | not on UA-nd | no EU letter-mail ban to GE found; Abkhazia postage ≠ letter stop | no | other-domain |
| HT Haiti | country | **sending not possible** DP-04 | **docs+goods suspended** CH-tr | non-served FR-sus | no acceptance UA-nd | EU-HTI (Reg 2022/2309) — **no letter-mail ban found**; multi-operator transport stop | candidate | operational (operator; not EU legal letter ban) |
| IQ Iraq | country | temp 07-28; not DP-04 stop | no IQ entry CH-tr | not on FR-sus | reopen UA-me | UN/EU arms-related — **no letter-mail ban found** | no | remove |
| IR Iran | country | ordinary DP-04; temp 07-28 DP-07 | **docs+goods+URGENT suspended** CH-tr | not on FR-sus | no acceptance UA-nd | EU Iran / UN = goods, dual-use, persons — **no letter-mail ban found** | no | provider-specific |
| KM Comoros | country | ordinary DP-04 | URGENT no CH-tr | not on FR-sus | no acceptance UA-nd | no EU/UN postal correspondence block identified | no | provider-specific |
| KP North Korea | country | **sending not possible** DP-04 | **docs+goods suspended** CH-tr | goods embargo; **docs OK** FR-sus | not on UA-nd | EU-KP / UN SCR 1718+ / BAFA-KP / SECO-KP = **goods & finance**, cargo inspect — **no correspondence prohibition identified**. FR permits docs; EU/UN correspondence prohibition not identified. | no (docs) | **legal** for goods frameworks if product includes goods; **provider-specific** for docs stop (DP/CH); do not emit global docs operational as “EU ban” |
| LY Libya | country | ordinary DP-04 | lithium goods only CH-tr | not on FR-sus | not on UA-nd | UN arms embargo — **no letter-mail ban found** | no | remove |
| MD Moldova | regions — Transnistria | ordinary MD; no letter routing rule | no MD entry CH-tr | delays; not suspended | not on UA-nd | no EU postal rule for Transnistria found | unclear | unresolved |
| MM Myanmar | country | unknown vs DP-04 table | URGENT no CH-tr | not on FR-sus | not on UA-nd | EU Myanmar goods/persons — **no letter-mail ban found**; need DP letter row | unclear | unresolved |
| MS Montserrat | country | ordinary DP-04 | no MS entry CH-tr | not on FR-sus | no acceptance UA-nd | no EU/UN postal correspondence block identified | no | provider-specific |
| PS Palestinian Territories | regions — Gaza / West Bank | no structured letter rule | no PS entry CH-tr | not on FR-sus | no acceptance UA-nd | no EU postal correspondence ban found | unclear | unresolved |
| RU Russia | country | no country stop | URGENT no; delays + lithium CH-tr | goods suspended; **docs OK** FR-sus | no acceptance UA-nd | **mail services not banned** EU-RU / OHCHR-PN | no | provider-specific (Ukrposhta acceptance; not EU letter ban) |
| SD Sudan | country | **sending not possible** DP-04 | URGENT no CH-tr | non-served / goods FR-sus | no acceptance UA-nd | EU-SDN / UN = targeted & goods where applicable — **no letter-mail ban found**; multi-operator stop | candidate | operational (operator; confirm CH docs vs URGENT-only) |
| SO Somalia | country | ordinary; no add-on services DP-04 | URGENT + PostPac no (docs unclear) CH-tr | suspended FR-sus | no acceptance UA-nd | UN arms embargo — **no letter-mail ban found** | no | provider-specific / other-domain |
| SS South Sudan | country | ordinary DP-04 | URGENT no CH-tr | non-served / goods embargo FR-sus | no acceptance UA-nd | UN/EU arms & goods measures — **no letter-mail ban found**; FR goods embargo ≠ docs ban | no | provider-specific |
| SY Syria | country | **sending not possible** DP-04 | URGENT no CH-tr | non-served + goods embargo FR-sus | no acceptance UA-nd | EU-SY goods/repression/arms (2025 easing of many sectorals) — **no letter-mail ban found**; FR still frames goods embargo | candidate | operational (operator stop) + optional **legal goods** if product ships goods; not “EU bans letters” |
| TC Turks and Caicos | country | ordinary DP-04 | no TC entry CH-tr | not on FR-sus | not on UA-nd | none identified | no | remove |
| TL Timor-Leste | country | ordinary DP-04 | no TL entry CH-tr | not on FR-sus | not on UA-nd | none identified | no | remove |
| TW Taiwan | country | ordinary DP-04 | no TW entry CH-tr | not on FR-sus | not on UA-nd | none identified | no | remove |
| UA Ukraine | regions — Crimea & Sevastopol (EU 692/2014); non-government-controlled areas of Donetsk, Luhansk, Kherson, Zaporizhzhia (EU 2022/263, 2022/1903); temporarily occupied territories (UA zakon); + weekly PLZ ops | **legal** regions + volatile PLZ DP-07 | delays; no region map CH-tr | Crimea/Sevastopol **goods** embargo; docs OK; served via PL FR-sus | outbound UA-nd N/A | **EU-UA / SECO / zakon** geographic measures = **legal**; weekly PLZ = not durable | yes (legal regions); no (weekly PLZ) | legal candidate (regions) — catalog impact needs a separate postal-consequence test; remove (weekly PLZ) |
| VE Venezuela | country | ordinary DP-04 | URGENT no CH-tr | not on FR-sus | not on UA-nd | EU person listings — **no letter-mail ban found** | no | remove |
| YE Yemen | country | **sending not possible** DP-04 | **docs+goods interrupted** CH-tr | suspended FR-sus | no acceptance UA-nd | EU-YEM targeted measures — **no letter-mail ban found**; multi-operator transport stop | candidate | operational (operator; not EU legal letter ban) |
| YT Mayotte | country | ordinary DP-04 | URGENT no CH-tr | FR overseas | not on UA-nd | FR territory — not an international ban | no | remove |

## Unclear after legal / regulatory verify

Only these still need more work (no letter-mail rule found; operator picture incomplete):

| Code | Why still unclear |
| --- | --- |
| MD | No EU/UN letter rule found; no sourced Transnistria ordinary-letter routing |
| MM | No letter-mail ban found in EU Myanmar measures; DP ordinary-letter row not confirmed this pass |
| PS | No EU letter-mail ban found; only UA-nd acceptance stop sourced |

All other former `unclear` rows are resolved as **provider-specific**, **other-domain**, **remove**, **operational (operator candidate)**, or **legal candidate (goods / UA geography)** — with the explicit rule: **sanctions / restrictive measures ≠ automatic letter-mail ban**.

## Notes

1. **Letter-mail ban:** not found in cited EU/UN sources for RU, BY, AF, IR, CF, LY, SO, SS, VE, HT, YE, SD, SY as *correspondence*. Goods / dual-use / persons / arms remain possible **legal** facts when the product surface includes goods (KP, SY, Crimea/Sevastopol).
2. **UA geography** is a **legal candidate** when grounded in EU-UA / SECO / zakon wording (do not substitute a single informal label for those source terms). Territorial measures alone do not establish a postal `block` / `warn`; catalog impact needs a separate postal-consequence test.
3. **CY** remains **routing** (destination handling), not a block.
4. **HT / YE / SD / SY** multi-operator stops are **operational candidates** only — multi-operator evidence is not by itself durability; historical snapshots over a sufficient period are still needed before `Durable? = yes`.
5. **KP docs:** FR permits docs; EU/UN correspondence prohibition not identified. DP/CH docs refusal is **provider-specific** relative to that evidence; do not label that refusal as EU/UN legal without a correspondence prohibition.
6. **RU / BY:** Consilium + OHCHR confirm mail is not banned at EU level; Ukrposhta stop is **Ukrposhta acceptance** policy, not a claim about Ukrainian state policy beyond that operator source.
