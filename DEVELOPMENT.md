# Development guide

Technical details for contributors: project structure, commands, and code quality.

## CI and coverage

- **Validation**: [porto-data-validation](https://github.com/gruncellka/porto-data/actions/workflows/porto-data-validation.yml)
- **Coverage**: [codecov](https://codecov.io/gh/gruncellka/porto-data)

## Project structure

```
porto-data/
├── porto_data/             # Data package (included in wheel)
│   ├── data/               # Main data files (JSON)
│   │   ├── products.json
│   │   ├── services.json
│   │   ├── prices.json
│   │   ├── zones.json
│   │   ├── weight_tiers.json
│   │   ├── dimensions.json
│   │   ├── restrictions.json
│   │   ├── features.json
│   │   └── data_links.json
│   ├── schemas/            # JSON schemas for validation
│   │   ├── products.schema.json
│   │   ├── services.schema.json
│   │   └── ...
│   ├── mappings.json
│   └── metadata.json       # Generated (do not edit)
├── cli/                    # CLI (porto command)
│   ├── main.py
│   └── commands/
├── scripts/                # Validation and utilities
│   ├── validators/
│   │   ├── schema.py
│   │   └── links.py
│   ├── data_files.py
│   ├── utils.py
│   └── generate_metadata.py
├── tests/                  # Test suite
├── resources/               # Source files (e.g. PPL CSV)
├── .pre-commit-config.yaml
├── Makefile
├── pyproject.toml
├── package.json             # npm package manifest
```

## Commands

### Porto CLI

| Command | Description |
|--------|-------------|
| `porto validate` | Validate everything (default) |
| `porto validate --type schema` | Validate JSON against schemas |
| `porto validate --type links` | Validate data_links.json consistency |
| `porto validate --type links --analyze` | Detailed links analysis |
| `porto metadata` | Generate metadata.json |

### Make

| Command | Description |
|--------|-------------|
| `make validate` | Validate all JSON (schema + links) |
| `make validate-data-links` | Validate data_links.json only |
| `make format` | Format JSON and Python |
| `make format-json` | Format JSON only |
| `make format-code` | Format Python only |
| `make lint` | Lint JSON and Python |
| `make lint-json` | Lint JSON only |
| `make lint-code` | Lint Python only |
| `make test` | Run tests |
| `make test-cov` | Tests with coverage (e.g. 80% threshold) |
| `make metadata` | Generate metadata.json |
| `make install-hooks` | Reinstall pre-commit hooks |
| `make help` | List all commands |

## Code quality

### JSON

- 4-space indentation
- Preserve key order (do not sort)
- Multi-line arrays for readability
- Format with Python `json.tool` (via `make format-json`)

### Python

- **Ruff**: formatting and linting (line length 100)
- **MyPy**: type checking
- Pre-commit hooks run format, lint, validate, and type-check on commit

## Testing

- Tests live in `tests/` and mirror the source layout.
- Run `make test` or `make test-cov` (coverage threshold configured in Makefile/pytest).
- Use fixtures from `tests/conftest.py` where applicable.

## Package publication

- **GitHub**: `gruncellka/porto-data`
- **npm**: `@gruncellka/porto-data` (scope @gruncellka)
- **PyPI**: `gruncellka-porto-data`

Both packages are built from the same source in a single publish workflow, so npm and PyPI ship the same data (same `data/`, `schemas/`, `mappings.json`, `metadata.json`).

**Release model**

- Version bump commit includes: `package.json`, `pyproject.toml`, and `CHANGELOG.md`.
- Git tag format: `vX.Y.Z`.
- CI publishes to npm and PyPI only from tagged release commits (see `.github/workflows/publish.yml`).

**Before you tag:** The **validation** workflow (`.github/workflows/validation.yml`) runs more checks than the publish workflow (format, structure, metadata, tests, lint, type-check). The publish workflow runs only on tag push and does a lighter validate + build. So **ensure the validation workflow has passed** on the commit you are about to tag; otherwise you may publish an unstable version. Manually confirm validation is green before creating the release tag.

## Version and releases

- **Version** is defined in `pyproject.toml` (Python) and `package.json` (npm). Keep them in sync for releases.
- **Bump both at once**: `bump2version patch` (or `minor` / `major`) updates both files and optionally commits and tags. Requires `pip install bump2version` or `make setup` (dev dependency). Config: `.bumpversion.cfg`.
- **Publishing** is done via the unified GitHub Actions workflow (tag `v*` or manual dispatch). Both npm and PyPI are built and validated first; publish runs only if both succeed. See `.github/workflows/publish.yml`.

**CI trigger pitfall:** Multiple `on:` triggers are OR’ed. So `push: tags: ['v*']` plus `workflow_run: workflows: ['validation']` would run publish on every validation completion (main/PR), not only after tag push. We do **not** use `workflow_run` for publish; trigger is tag `v*` and workflow_dispatch only. If you add `workflow_run` later, require a hard guard that the validation run’s `head_sha` has a tag matching `v*`, else skip.
