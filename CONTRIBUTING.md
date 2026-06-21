# Contributing to Porto Data

## Published packages vs this repo

**npm** (`@gruncellka/porto-data`) and **PyPI** (`gruncellka-porto-data`) carry the **same** dataset: `porto_data/policy/`, `porto_data/formats/`, `porto_data/providers/<id>/`, `porto_data/schemas/`, `mappings.json`, `metadata.json`. It is **cross-platform** (JSON + schemas only, no compiled code).

The **`porto` CLI**, **`cli/`**, and **`scripts/`** validators run **only here** (and in CI)—they are **not** included in the published packages. Consumers read the JSON; contributors use this repo to edit and validate.

**Invariant:** keys in **`providers.json`** must match directory names under **`porto_data/providers/<id>/`** and keys under **`mappings.json` → `providers`**.

## Setup

```bash
make setup
```

Creates `venv`, dev dependencies, and pre-commit hooks.

## Where files live

| Area                              | Path                                                                                                             |
| --------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| Shared across providers           | `porto_data/policy/*.json`, `porto_data/formats/*.json`, and bundle-root `providers.json` |
| Per operator                      | `porto_data/providers/<provider_id>/*.json` and `.../prices/*.json` (e.g. `products.json`, `graph.json`, `prices/products.json`, `prices/services.json`, `limits.json`) |
| Schemas                           | `porto_data/schemas/*.json`                                                                                      |
| Which entities exist per provider | `porto_data/mappings.json`                                                                                       |
| Generated manifest + checksums    | `porto_data/metadata.json` — **never edit by hand**; run `make metadata`                                         |

Cross-file structure and product→zone→tier wiring live in each provider’s **`graph.json`** (`file_type`: `graph`), including top-level **`edges`** (not `links`). Legacy flat `porto_data/data/` and `data_links.json` are gone.

## Typical loop

1. Edit JSON and/or schemas.
2. `make validate` then `make format`.
3. Commit. If hooks regenerate metadata, include it: `git add porto_data/metadata.json`.

## Commands

**Default validation order:** schema → layout (mappings, registry, metadata checks) → limits → graph (all providers).

| CLI                                     | Purpose                                            |
| --------------------------------------- | -------------------------------------------------- |
| `porto validate`                        | Full chain above                                   |
| `porto validate --type schema`          | Schema vs JSON                                     |
| `porto validate --type mappings`        | `mappings.json`, provider dirs, registry, metadata |
| `porto validate --type limits`          | `providers/*/limits.json`                          |
| `porto validate --type graph`           | `graph.json` (incl. `edges`)                       |
| `porto validate --type graph --analyze` | Verbose graph report                               |
| `porto metadata`                        | Regenerate `metadata.json`                         |

| Make                                            | Purpose                               |
| ----------------------------------------------- | ------------------------------------- |
| `make validate`                                 | Same as full `porto validate`         |
| `make validate-graph`                           | Graph only                            |
| `make format` / `make lint` / `make type-check` | Quality                               |
| `make test` / `make test-cov`                   | Tests (90% coverage gate)             |
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
