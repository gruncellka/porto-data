# Contributing to Porto Data

## Setup

1. Clone the repository and enter the project directory.
2. Run:
   ```bash
   make setup
   ```
   This installs a Python venv, the `porto` CLI, dev dependencies (ruff, mypy, pytest, pre-commit), and pre-commit hooks.
3. Pre-commit hooks run automatically on every commit.

## Making changes

Data files are in `data/`; open any `.json` to view. To edit:

1. Edit JSON files under `data/` (and `schemas/` if needed).
2. Validate: `make validate`
3. Format: `make format`
4. Commit. If `metadata.json` was regenerated, stage it in the same commit: `git add metadata.json`
5. If the commit fails because `metadata.json` is out of date, run `make metadata`, then `git add metadata.json` and commit again.

## Validation

- `make validate` — Validate all JSON against schemas and `data_links.json`.
- `porto validate --type schema` — Schema validation only.
- `porto validate --type links` — Data links consistency.
- `porto validate --type links --analyze` — Detailed links analysis.

**What links validation checks:** All products, zones, and weight tiers in links exist in their respective files; product zones and weight tiers match between `data_links.json` and `products.json`; prices exist for all zone+weight_tier combinations; available services are valid and have prices; lookup method configuration matches actual file structure; unit values (weight, dimension, price, currency) are consistent; all data files are covered in dependencies; no circular dependencies.

## Pre-commit hooks

Hooks run on every commit and:

- Format JSON and Python
- Validate JSON syntax and schemas
- Lint and type-check Python
- Regenerate `metadata.json` when data/schemas change

If `metadata.json` is regenerated but not staged, the commit is **rejected**. Always stage `metadata.json` in the same commit as data changes.

## metadata.json

- Auto-generated; do not edit by hand.
- Contains checksums and canonical schema URLs for each entity.
- Regenerated when files in `data/` or `schemas/` change.
- Must be committed whenever it changes (same commit as the data/schema changes).

## Schema mapping

Schema-to-data mappings are in `mappings.json`. Data files use a `$schema` property with the canonical schema URL (GitHub). Validators can resolve schemas from the package paths using `metadata.json` or `mappings.json`.

## Adding or updating data

- **New data**: Add to the right JSON file under `data/`, ensure it matches the schema, run `make validate` and `make format`, then commit (with `metadata.json` if it changed).
- **Schema changes**: Edit the schema in `schemas/`, update data in `data/`, run `make validate`.

## Pull requests

1. Fork the repo and create a branch.
2. Run `make setup` and `make quality` before pushing.
3. Ensure pre-commit passes (it runs on commit).
4. Open a PR. CI runs validation and tests.

## Releasing (version bump)

Before a release, bump the version in both `package.json` and `pyproject.toml`, and update `CHANGELOG.md`. Use **bump2version** so both files stay in sync: run `bump2version patch` (or `minor` / `major`) after `make setup`. See [DEVELOPMENT.md](DEVELOPMENT.md) for details and the release model.

**Notice:** Before creating a release tag, ensure the **validation** workflow (`.github/workflows/validation.yml`) has passed on your branch. The publish workflow runs on tag push with fewer checks; if you tag without validation being green, you may publish an unstable version.

For the full list of make/porto commands and project structure, see [DEVELOPMENT.md](DEVELOPMENT.md).
