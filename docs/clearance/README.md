# Franking zone and clearance

**Focus: Deutsche Post Internetmarke.** Docs only — no catalog invent for unintegrated providers.

Confidence: **verified** = operator quote + URL · **measured** = live checkout · **omit** = correctly absent.

Prefer / Licko composition inset is **not** porto-data.

---

## Vocabulary

| Term | Meaning | Field |
|------|---------|-------|
| **placement** | Operator franking **zone** (reserved area). Not free drag. Not “print flush to the edge”. | `placement.envelopes[id]` |
| **size** | Mark footprint | `profiles[].size` |
| **clearance** | Quiet band **around the graphic** only if the operator says so | `profiles[].clearance` (omit if none) |
| **edge silence** | Distance from **paper edge** — **≠** clearance | encode only with evidence |

ISO/DIN/DSTU/UPU do **not** define franking mm. SDK passes catalog through.

---

## Deutsche Post (integrated)

| Field | Catalog | Confidence |
|-------|---------|------------|
| `placement` | **74×40** TR flush (`x = face−74`, `y: 0`) on DL/C6/C5/C4/B4 | **verified** — [Frankiervermerk-Merkblatt](https://www.deutschepost.de/dam/jcr:faf94e36-9cf8-44eb-97f5-2392748ecfc5/dp-frankiervermerk-merkblatt-202607.pdf); [Automationsfähige Briefsendungen](https://www.deutschepost.de/dam/dpag/images/P_p/printmailing/downloads/dp-automationsfaehige-briefsendungen.pdf) |
| `size` | 37×20 · 62×20 · 62×33 | **measured** — IM calibrations DPI300 (reg-intl cal **32.5** vs profile **33**) |
| `clearance` | omit | [IM FAQ](https://www.deutschepost.de/de/i/internetmarke-porto-drucken/haeufige-fragen/frankieren-ausgabeformate.html): upper right, **no** mm. Merkblatt **5 mm** “sollte” = **Frankierwelle**, not IM footprint clearance |

Do not invent `clearance`. Composition inset (if any) stays in Licko; fit-check per profile. Detail: [providers/deutschepost.md](providers/deutschepost.md#envelope-franking-placement).

---

## Other providers (docs note only — no data change)

| Provider | Catalog today | Note |
|----------|---------------|------|
| **laposte** | placement 74×40; size 64×34; clearance omit | Guide 2025 **10 mm** is mécanisable/industriel — do not encode into consumer MTEL or release unintegrated invent |
| **swisspost** | placement 74×38; size 40×40; clearance omit | Mask zone **verified** 74×38; **40×40** not proven as face stamp (public WebStamp = labels). Validator skip is debt — **do not** “fix” in catalog until measured |
| **ukrposhta** | placement omit; label size | Correct omit |

---

## Encoding rules (when changing data later)

1. Zone from right → `x = face_width − zone_width`.
2. Graphic quiet → `clearance` only.
3. Edge silence ≠ clearance.
4. No Prefer/Licko constants in porto-data.
5. No permanent validator skip without an evidence-backed contract.
