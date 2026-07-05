# Contributing to Porto Data

## Published packages vs this repo

**npm** (`@gruncellka/porto-data`) and **PyPI** (`gruncellka-porto-data`) ship **only** the dataset: `porto_data/policy/`, `porto_data/formats/`, `porto_data/providers/<id>/`, `porto_data/schemas/`, `mappings.json`, `metadata.json`. Cross-platform JSON + schemas — **no resolver, no SDK logic**.

**This repository** adds contributor tooling that is **not** published:

| In repo | In published package |
|---------|----------------------|
| JSON data + schemas | Yes |
| `scripts/` validators | No (CI + `make validate` only) |
| `cli/` (`porto validate`, …) | No |
| Resolution / `markLayout` code | No — **Porto SDK** repos |

Consumers (SDK, apps) read the JSON. Contributors edit data here and run validators before release.

**Invariant:** keys in **`providers.json`** must match directory names under **`porto_data/providers/<id>/`** and keys under **`mappings.json` → `providers`**.

## Getting started

```bash
make
```

First run of **`make`** creates `venv`, installs dev dependencies, and installs pre-commit hooks. You stay in your shell — **`make validate`**, **`make quality`**, etc. run inside the venv automatically. Manual `source venv/bin/activate` is only if you run `python` / `pytest` / `porto` directly without `make`. For CI, use **`make venv`** (setup only, no hooks).

## Where files live

| Area                              | Path                                                                                                             |
| --------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| Shared across providers           | `porto_data/policy/*.json`, `porto_data/formats/*.json`, and bundle-root `providers.json` |
| Per operator                      | `porto_data/providers/<provider_id>/*.json` and `.../prices/*.json` (e.g. `products.json`, `graph.json`, `prices/products.json`, `prices/services.json`, `limits.json`) |
| Schemas                           | `porto_data/schemas/*.json`                                                                                      |
| Which entities exist per provider | `porto_data/mappings.json`                                                                                       |
| Generated manifest + checksums    | `porto_data/metadata.json` — **never edit by hand**; run `make metadata`                                         |

Cross-file structure lives in each provider’s **`graph.json`** (`edges.products`, `edges.marks`, `services`, `dependencies`). Legacy paths (`porto_data/data/`, `data_links.json`, graph `links` / `lookup_rules` / …) are removed — see `.cursorrules` layout.

## Vocabulary (canonical names)

| Concept | Name |
| ------- | ---- |
| Weight bracket file | `weights.json` (`file_type`: `weights`) |
| Single tier field | `weight_tier` |
| Conditional rules file | `rules.json` (`file_type`: `provider_rules`) |

**Provider order:** `deutschepost` → `ukrposhta` → `laposte` → `swisspost` in prose, tables, and JSON keys — see `.cursorrules`.

**JSON naming (Porto-owned keys):** `.cursorrules` § JSON naming doctrine — enforced by validators and Bugbot rules 19–21.

## Reference direction (frozen)

1. **SDK / app input** → `porto_id` (canonical enum in `schemas/porto_ids.schema.json`).
2. **graph.json, prices, rules** → native **`id`** only (never `porto_id`).
3. **`native_id`** → carrier API catalog code only.
4. **`porto_id` on catalog rows** → cross-operator normalization on products, services, features.
5. **`services[].features`** → convention under review; do not enforce until provider audit completes.

Disambiguation when multiple native rows share one `porto_id`: [docs/resolution.md](docs/resolution.md). Provider file checklist: [docs/provider-template.md](docs/provider-template.md). **Tariff amounts:** [docs/tariff-verification.md](docs/tariff-verification.md) and [docs/providers/](docs/providers/) — reconcile against official sources; `make validate` does not check cent amounts.

## Typical loop

1. Edit JSON and/or schemas.
2. `make validate` then `make format` (or just `make` for the full gate).
3. Commit. If hooks regenerate **`porto_data/metadata.json`** or **`docs/porto_id.md`**, include those files in the commit (pre-commit stages both when catalog data changes).

## Commands

**Default validation order:** schema → mappings → markets → limits → porto_ids → delivery → graph (all providers).

| CLI                                     | Purpose                                            |
| --------------------------------------- | -------------------------------------------------- |
| `porto validate`                        | Full chain above                                   |
| `porto validate --type schema`          | Schema vs JSON                                     |
| `porto validate --type mappings`        | `mappings.json`, provider dirs, registry, metadata |
| `porto validate --type markets`         | `policy/markets.json` vs provider countries        |
| `porto validate --type limits`          | `providers/*/limits.json`                          |
| `porto validate --type porto_ids`       | `porto_id` enums, native-id cross-file refs; regenerates **`docs/porto_id.md`** (must be committed) |
| `porto validate --type delivery` | Zone-scoped **`delivery[]`**, optional **`included_features[]`** / **`indemnity`**, twin resolution fingerprint |
| `porto validate --type graph`           | `graph.json` (incl. `edges.products`, `edges.marks`) |
| `porto validate --type graph --analyze` | Verbose graph report                               |
| `porto metadata`                        | Regenerate `metadata.json`                         |

| Make                                            | Purpose                               |
| ----------------------------------------------- | ------------------------------------- |
| `make`                                          | venv + hooks                          |
| `make venv`                                     | venv + dev deps only (CI)             |
| `make validate`                                 | Same as full `porto validate`         |
| `make validate-graph`                           | Graph only                            |
| `make format` / `make lint` / `make type-check` | Quality                               |
| `make test` / `make test-cov`                   | Tests (**100%** coverage gate on `scripts/` + `cli/`) |
| `make metadata`                                 | Regenerate metadata                   |
| `make quality`                                  | validate + format + lint + type-check |

## Pre-commit

Hooks may format, validate, lint, type-check, and refresh `metadata.json`. If they change files, re-stage and commit again. Unstaged `metadata.json` after regeneration fails the commit by design.

## PRs and CI

Use a branch; ensure pre-commit passes. CI runs validation, format checks, metadata consistency, tests, lint, and MyPy.

## Releases

1. Update `CHANGELOG.md`.
2. Bump version in `package.json` and `pyproject.toml` (e.g. `bump2version`).
3. `metadata.json` committed and current.
4. Tag `vX.Y.Z` on `main` (or your release process) to trigger publish; see `.github/workflows/publish.yml`.

Packages: npm `@gruncellka/porto-data`, PyPI `gruncellka-porto-data`.
