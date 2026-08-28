# Contributing to Porto Data

## Repository model

**npm** (`@gruncellka/porto-data`) and **PyPI** (`gruncellka-porto-data`) ship **only** the dataset: `porto_data/policy/`, `porto_data/formats/`, `porto_data/providers/<id>/`, `porto_data/schemas/`, `mappings.json`, `metadata.json`. JSON + schemas — **no resolver**. Catalog layering: [docs/identity.md](docs/identity.md).

**This repository** adds contributor tooling that is **not** published: `scripts/` validators, `cli/` (`porto validate`, …).

Contributors edit data here and run validators before release.

**Invariant:** keys in **`providers.json`** must match directory names under **`porto_data/providers/<id>/`** and keys under **`mappings.json` → `providers`**.

## Setup

```bash
make
```

First run creates `venv`, installs dev dependencies, and installs pre-commit hooks. Later `make` targets use the venv automatically. Activate the venv only if you run `python` / `pytest` / `porto` without `make`.

## Data layout

| Area | Path |
| ---- | ---- |
| Shared across providers | `porto_data/policy/*.json`, `porto_data/formats/*.json`, bundle-root `providers.json` |
| Per provider | `porto_data/providers/<id>/*.json` and `.../prices/*.json` — [docs/template.md](docs/template.md) |
| Schemas | `porto_data/schemas/*.json` |
| Which entities exist per provider | `porto_data/mappings.json` |
| Generated manifest + checksums | `porto_data/metadata.json` — **never edit by hand**; run `make metadata` |

Cross-file structure lives in each provider’s **`graph.json`**. Locate entities via **`mappings.json`** / **`metadata.json`** — not hard-coded relative paths.

## Data contract

| Concept | Name |
| ------- | ---- |
| Weight bracket file | `weights.json` (`file_type`: `weights`) |
| Single tier field | `weight_tier` |
| Conditional rules file | `rules.json` (`file_type`: `provider_rules`) |
| Address forms | `formats/addresses.json` (`file_type`: `addresses`) — [docs/formats.md](docs/formats.md) |
| Wire channel | `graph.edges.wire` / `execution.json` `wire` |
| Billing / execution tokens | `execution.json` `billing[]` / `execution[]` (`wallet`, `mark`) |
| Product tracking posture | `products.tracking` (`none` \| `optional` \| `included`) |

**Provider order:** Deutsche Post, Ukrposhta, La Poste, Swiss Post — same order in prose, tables, and JSON keys.

**JSON naming (Porto-owned keys):** `.cursorrules` § JSON naming doctrine.

### Reference direction (frozen)

1. **Lookup dimensions** → destination, weight, optional envelope, optional product `id`, optional service `id` or `kind`. Envelope membership: [docs/matrix.md](docs/matrix.md).
2. **graph.json, prices, rules** → concrete **`id`** only (never `kind`).
3. **Wire / checkout codes** → runtime / `graph.edges.wire` only (not a field on product or service rows).
4. **`kind` on services/features** → cross-provider grouping only. Products have no `kind`. See [docs/id.md](docs/id.md).
5. **`services[].features`** → each entry is a `features.json` `id`.

Disambiguation when multiple products share zone + weight: [docs/resolution.md](docs/resolution.md).

**Marks calibrations:** `calibrations[].mark_profile` is the wire checkout layout token (`FRANKING_ZONE` / `ADDRESS_ZONE`). Porto profile ids live in `profiles[]` and `by_mark_profile` keys. See [docs/marks.md](docs/marks.md).

**Tariff dating (catalog baseline):** In **`providers/<id>/products.json`**, **`prices/products.json`**, and **`prices/services.json`**, **`effective_from`** is the **bundle baseline** (**`2026-01-01`**) for the modeled **2026** tariff snapshot. Use **`effective_to`**: **`null`** until a row is superseded by a newer **`price[]`** entry. (Other files, e.g. **`policy/restrictions.json`**, keep their own effective-dating semantics.)

**Tariff amounts:** CI validates structure only — not that amounts match live carrier tables. `make validate` does not check cent amounts. Reconciliation: [docs/tariffs.md](docs/tariffs.md).

## Workflow

1. Edit JSON and/or schemas.
2. `make validate`, then `make format` (or `make quality` for the full local gate).
3. If hooks regenerate **`porto_data/metadata.json`** or **`docs/kinds.md`**, include those files in the commit.
4. Commit.

## Commands

**Default `porto validate` order:** schema → mappings → markets → addresses → kinds → delivery → graph. Make targets wrap the CLI; use `porto validate --type …` for a single stage.

| CLI | Purpose |
| --- | ------- |
| `porto validate` | Full chain above |
| `porto validate --type schema` | Schema vs JSON |
| `porto validate --type mappings` | `mappings.json`, provider dirs, registry, metadata |
| `porto validate --type markets` | `policy/markets.json` vs provider countries |
| `porto validate --type addresses` | `formats/addresses.json` vs layouts/jurisdictions |
| `porto validate --type kinds` | service/feature kinds; regenerates **`docs/kinds.md`** |
| `porto validate --type delivery` | Zone-scoped **`delivery[]`**, optional **`included_features[]`** / **`indemnity`** |
| `porto validate --type graph` | `graph.json` (incl. `edges.products`, `edges.marks`) |
| `porto validate --type graph --analyze` | Verbose graph report |
| `porto metadata` | Regenerate `metadata.json` |

| Make | Purpose |
| ---- | ------- |
| `make` | venv + hooks |
| `make venv` | venv + dev deps only (CI) |
| `make help` | Show all commands |
| `make validate` | Full `porto validate` chain |
| `make schema` … `make graph` | Single validation stage (see `make help`) |
| `make format` / `make lint` / `make types` | Quality |
| `make test` / `make test-cov` | Tests (**100%** coverage gate on `scripts/` + `cli/`) |
| `make metadata` | Regenerate metadata (`CHECK=1` to verify committed copy) |
| `make quality` | validate + format + lint + types |
| `make artifact` | build npm+PyPI once, verify, smoke (keeps tarball + `dist/`) |

## CI and pre-commit

CI job names match Make concerns: `schema`, `format`, `lint`, `types`, `test`, `mappings`, `markets`, `addresses`, `kinds`, `delivery`, `graph`, `metadata`, and aggregate **`validate`** (branch-protection check). CI is Make; hooks are local; `CHECK=1` is how CI proves the committed tree already matches (`make format CHECK=1`, `make metadata CHECK=1`).

Hooks may format, validate, lint, types-check, and refresh `metadata.json`. If they change files, re-stage and commit again. Unstaged `metadata.json` after regeneration fails the commit by design.

## Releases

`main` is the integration branch. Packages: npm `@gruncellka/porto-data`, PyPI `gruncellka-porto-data`.

1. Integrate on `main`; accumulate `[Unreleased]` in `CHANGELOG.md`. Do not tag while feature work is still landing.
2. Cut `release/X.Y.Z` from stable `main` (CI green).
3. On the release branch: dated changelog; `bump2version` (`tag = False` in `.bumpversion.cfg`; commit `release: vX.Y.Z`); `make metadata`; `make quality` and `make test-cov`.
4. Tag `vX.Y.Z` manually; push branch and tag. Tag push triggers `.github/workflows/publish.yml`.
5. Merge the release branch back to `main`.

A direct bump + tag on `main` is acceptable only for small, isolated fixes when no other PRs are in flight.
