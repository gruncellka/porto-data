# Contributing to Porto Data

Porto Data is a data repository (JSON + schemas) with Python tooling for validation and packaging.

## Quick start

1. Clone the repository and enter the project directory.
2. Run:
    ```bash
    make setup
    ```
3. Start making changes. Pre-commit hooks run automatically on every commit.

`make setup` creates `venv`, installs dev dependencies, and installs pre-commit hooks.

## What to edit

- Data files: `porto_data/data/*.json`
- Schemas: `porto_data/schemas/*.json`
- Schema/data mapping: `porto_data/mappings.json`
- Generated metadata: `porto_data/metadata.json` (do not edit by hand)

## Daily workflow

1. Edit data and/or schema files.
2. Run `make validate`.
3. Run `make format`.
4. Commit changes.
5. If `porto_data/metadata.json` changed, stage it in the same commit.

If a commit fails because metadata is out of date, run:

```bash
make metadata
git add porto_data/metadata.json
```

## Most useful commands

### Porto CLI

| Command                                 | Description                     |
| --------------------------------------- | ------------------------------- |
| `porto validate`                        | Validate everything (default)   |
| `porto validate --type schema`          | Validate JSON against schemas   |
| `porto validate --type links`           | Validate data links consistency |
| `porto validate --type links --analyze` | Detailed links analysis         |
| `porto metadata`                        | Regenerate `metadata.json`      |

### Make

| Command                    | Description                                   |
| -------------------------- | --------------------------------------------- |
| `make help`                | Show all commands                             |
| `make validate`            | Validate schemas and links                    |
| `make validate-data-links` | Validate `data_links.json` only               |
| `make format`              | Format JSON and Python                        |
| `make lint`                | Lint JSON and Python                          |
| `make type-check`          | Run MyPy                                      |
| `make test`                | Run tests                                     |
| `make test-cov`            | Run tests with coverage                       |
| `make metadata`            | Regenerate `metadata.json`                    |
| `make test-publish`        | Build and verify npm + PyPI artifacts locally |

## Pre-commit behavior

On commit, hooks can format files, run validation/lint/type-check, and regenerate `metadata.json`.

If hooks modify files, re-stage and commit again.
If `metadata.json` is regenerated but not staged, the commit is rejected.

## Pull requests

1. Create a branch.
2. Run `make setup` once.
3. Ensure commits pass pre-commit checks.
4. Open a PR.

CI runs:

- JSON validation
- Data links validation
- Formatting checks
- Metadata verification
- Python lint + type-check
- Tests with coverage upload

## Releases

### Version bump

Before a release:

1. Update `CHANGELOG.md`.
2. Bump version in both `package.json` and `pyproject.toml` (recommended: `bump2version patch` / `minor` / `major`).
3. `bump2version` creates the version commit but does not create a git tag automatically (`tag = False`).
4. Create the release tag manually after merge on `main` (recommended), for example: `git tag vX.Y.Z && git push origin vX.Y.Z`.
5. Ensure `porto_data/metadata.json` is current and committed.

### Publishing

Publish workflow: `.github/workflows/publish.yml`

- Trigger by manual tag push `v*` (normal release), or
- Run manually via GitHub Actions (`workflow_dispatch`)

Manual dispatch supports `publish_target` (`both`, `npm`, `pypi`) for retry scenarios.

Packages:

- GitHub repo: `gruncellka/porto-data`
- npm: `@gruncellka/porto-data`
- PyPI: `gruncellka-porto-data`

Before tagging, make sure validation CI is green for the exact commit you will release.
Recommended flow: release branch -> PR to `main` -> manual tag on `main` -> publish workflow.

## CI links

- Validation workflow: [validation](https://github.com/gruncellka/porto-data/actions/workflows/validation.yml)
- Publish workflow: [publish](https://github.com/gruncellka/porto-data/actions/workflows/publish.yml)
- Coverage: [codecov](https://codecov.io/gh/gruncellka/porto-data)
