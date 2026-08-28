.PHONY: . help venv install-hooks
.PHONY: schema mappings markets addresses kinds delivery graph
.PHONY: format lint types test test-cov metadata validate quality artifact

# Prefer Python 3.13+ (project requires >=3.13). Override in CI: PYTHON3=python
PYTHON3 ?= $(shell command -v python3.13 2>/dev/null || command -v python3 2>/dev/null || echo python3)
export PYTHON3

VENV := venv
VENV_PYTHON := $(VENV)/bin/python
VENV_MARKER := $(VENV)/.setup-complete

JSON_PATHS = porto_data/*.json porto_data/schemas/*.json porto_data/policy/*.json porto_data/formats/*.json porto_data/providers/*/*.json porto_data/providers/*/prices/*.json

# Plain `make`
.DEFAULT_GOAL := .

.: venv install-hooks
	@echo "✓ Ready — make targets use venv automatically (no source needed)"

help:
	@echo "Porto Data — validation & quality"
	@echo "=================================="
	@echo ""
	@echo "  make               - venv + dev deps + pre-commit hooks"
	@echo "  make help          - Show this help"
	@echo "  make venv          - venv + dev deps only (CI / scripts)"
	@echo ""
	@echo "Validation (porto validate stages):"
	@echo "  make validate      - schema → mappings → markets → addresses → kinds → delivery → graph"
	@echo "  make schema        - JSON vs schemas"
	@echo "  make mappings      - mappings.json, registry, metadata alignment"
	@echo "  make markets       - policy/markets.json"
	@echo "  make addresses     - formats/addresses.json"
	@echo "  make kinds         - service/feature kinds (+ docs/kinds.md freshness)"
	@echo "  make delivery      - zone delivery SLAs"
	@echo "  make graph         - provider graph.json"
	@echo "  make metadata      - regenerate metadata.json (CHECK=1 to verify committed copy)"
	@echo ""
	@echo "Quality:"
	@echo "  make format        - JSON + Python (CHECK=1 for read-only)"
	@echo "  make lint          - JSON syntax + Ruff"
	@echo "  make types         - MyPy on scripts/ + cli/"
	@echo "  make test          - pytest"
	@echo "  make test-cov      - pytest + coverage reports"
	@echo "  make quality       - validate + format + lint + types"
	@echo ""
	@echo "Publish:"
	@echo "  make artifact      - build npm+PyPI once, verify, smoke (keeps tarball + dist/)"
	@echo ""

venv:
	@if [ ! -x "$(VENV_PYTHON)" ] || [ ! -f "$(VENV_MARKER)" ]; then \
		echo "Setting up porto-data (venv + dev deps)..."; \
		$(PYTHON3) -m venv $(VENV) || (echo "Error: need Python >=3.13 ($(PYTHON3) failed)" && exit 1); \
		. $(VENV)/bin/activate && pip install -q -U pip && pip install -q ".[dev]"; \
		touch $(VENV_MARKER); \
		echo "✓ Ready"; \
	fi

install-hooks: venv
	@if git rev-parse --is-inside-work-tree > /dev/null 2>&1; then \
		echo "Installing pre-commit hooks..."; \
		if [ -f $(VENV)/bin/pre-commit ]; then \
			$(VENV)/bin/pre-commit install; \
		else \
			echo "Error: pre-commit not found."; \
			exit 1; \
		fi; \
		echo "✓ Pre-commit hooks installed"; \
	fi

validate: venv schema mappings markets addresses kinds delivery graph

schema: venv
	@. $(VENV)/bin/activate && PYTHONPATH=. python -m cli.main validate --type schema

mappings: venv
	@. $(VENV)/bin/activate && PYTHONPATH=. python -m cli.main validate --type mappings

markets: venv
	@. $(VENV)/bin/activate && PYTHONPATH=. python -m cli.main validate --type markets

addresses: venv
	@. $(VENV)/bin/activate && PYTHONPATH=. python -m cli.main validate --type addresses

kinds: venv
	@. $(VENV)/bin/activate && PYTHONPATH=. python -m cli.main validate --type kinds
	@if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then \
		if [ -n "$$(git diff docs/kinds.md)" ]; then \
			echo "❌ docs/kinds.md is out of date. Run 'make kinds' and commit the updated file."; \
			git diff docs/kinds.md; \
			exit 1; \
		fi; \
	fi

delivery: venv
	@. $(VENV)/bin/activate && PYTHONPATH=. python -m cli.main validate --type delivery

graph: venv
	@. $(VENV)/bin/activate && PYTHONPATH=. python -m cli.main validate --type graph

format: venv
	@if [ -n "$(CHECK)" ]; then echo "Checking formatting..."; else echo "Formatting..."; fi
	@for file in $(JSON_PATHS); do \
		if [ -f "$$file" ]; then \
			if [ -n "$(CHECK)" ]; then \
				$(PYTHON3) scripts/format_json_file.py --check "$$file" || exit 1; \
			else \
				$(PYTHON3) scripts/format_json_file.py "$$file" || exit 1; \
			fi; \
		fi; \
	done
	@if [ -n "$(CHECK)" ]; then \
		. $(VENV)/bin/activate && ruff format --check . || exit 1; \
	else \
		. $(VENV)/bin/activate && ruff format . && ruff check --fix . || exit 1; \
	fi

lint: venv
	@for file in $(JSON_PATHS); do \
		if [ -f "$$file" ]; then \
			$(PYTHON3) -m json.tool "$$file" > /dev/null || (echo "✗ $$file: JSON syntax error" && exit 1); \
		fi; \
	done
	@. $(VENV)/bin/activate && ruff check .

types: venv
	@. $(VENV)/bin/activate && PYTHONPATH=. mypy scripts/ cli/

test: venv
	@. $(VENV)/bin/activate && PYTHONPATH=. pytest

test-cov: venv
	@. $(VENV)/bin/activate && PYTHONPATH=. pytest --cov-report=html --cov-report=xml

metadata: venv
	@. $(VENV)/bin/activate && PYTHONPATH=. python -m cli.main metadata
	@if [ -n "$(CHECK)" ] && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then \
		if [ -n "$$(git diff porto_data/metadata.json)" ]; then \
			echo "❌ metadata.json is out of date. Run 'make metadata' and commit."; \
			git diff porto_data/metadata.json; \
			exit 1; \
		fi; \
	fi

quality: venv validate format lint types

artifact: venv
	@./scripts/release/verify_artifact.sh
