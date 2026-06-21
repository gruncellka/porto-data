.PHONY: help ensure-venv install-hooks
.PHONY: validate-json validate-graph format-json lint-json format-code lint-code type-check
.PHONY: validate format lint metadata test test-cov quality test-publish

# Default: full quality gate (creates venv on first run)
.DEFAULT_GOAL := quality

# Prefer Python 3.13+ (project requires >=3.13). Override in CI: PYTHON3=python
PYTHON3 ?= $(shell command -v python3.13 2>/dev/null || command -v python3 2>/dev/null || echo python3)
export PYTHON3

VENV := venv
VENV_PYTHON := $(VENV)/bin/python
VENV_MARKER := $(VENV)/.setup-complete

help:
	@echo "Porto Data - Schema Validation & Code Quality"
	@echo "=============================================="
	@echo ""
	@echo "Default:"
	@echo "  make               - validate + format + lint + type-check (creates venv if needed)"
	@echo "  make help          - Show this help"
	@echo ""
	@echo "Most Common Commands:"
	@echo "  make validate      - Validate all JSON (schema → mappings → limits → porto_ids → graph)"
	@echo "  make format        - Format JSON and Python"
	@echo "  make lint          - Lint JSON and Python"
	@echo "  make quality       - Same as default make"
	@echo ""
	@echo "JSON Commands:"
	@echo "  make validate-json  - Full JSON validation chain"
	@echo "  make validate-graph - graph.json only"
	@echo "  make format-json    - Format JSON (CHECK=1 for read-only)"
	@echo "  make lint-json      - JSON syntax check"
	@echo ""
	@echo "Code Commands:"
	@echo "  make format-code    - Ruff format (CHECK=1 for read-only)"
	@echo "  make lint-code      - Ruff lint"
	@echo "  make type-check     - MyPy"
	@echo ""
	@echo "Testing:"
	@echo "  make test           - Run tests"
	@echo "  make test-cov       - Tests with coverage"
	@echo ""
	@echo "Metadata:"
	@echo "  make metadata       - Regenerate metadata.json"
	@echo ""
	@echo "Publish:"
	@echo "  make test-publish   - npm + PyPI install smoke test"
	@echo ""

# ==========================================
# Virtualenv (internal — triggered by other targets)
# ==========================================
ensure-venv:
	@if [ ! -x "$(VENV_PYTHON)" ] || [ ! -f "$(VENV_MARKER)" ]; then \
		echo "Setting up porto-data (venv + dev deps)..."; \
		$(PYTHON3) -m venv $(VENV) || (echo "Error: need Python >=3.13 ($(PYTHON3) failed)" && exit 1); \
		. $(VENV)/bin/activate && pip install -q -U pip && pip install -q ".[dev]"; \
		touch $(VENV_MARKER); \
		if git rev-parse --is-inside-work-tree > /dev/null 2>&1; then \
			$(MAKE) install-hooks || echo "Warning: pre-commit hooks not installed."; \
		fi; \
		echo "✓ Ready"; \
	fi

# ==========================================
# Most Common Commands
# ==========================================
validate: ensure-venv validate-json

format: ensure-venv format-json format-code

lint: ensure-venv lint-json lint-code

# ==========================================
# JSON Commands
# ==========================================
validate-json: ensure-venv
	@echo "Validating JSON against schemas..."
	@. $(VENV)/bin/activate && PYTHONPATH=. python -m cli.main validate --type schema
	@echo "Validating mappings (mappings.json, registry, metadata, stray files)..."
	@. $(VENV)/bin/activate && PYTHONPATH=. python -m cli.main validate --type mappings
	@echo "Validating policy/markets.json..."
	@. $(VENV)/bin/activate && PYTHONPATH=. python -m cli.main validate --type markets
	@echo "Validating providers/*/limits.json..."
	@. $(VENV)/bin/activate && PYTHONPATH=. python -m cli.main validate --type limits
	@echo "Validating porto_id vocabulary and native-id refs..."
	@. $(VENV)/bin/activate && PYTHONPATH=. python -m cli.main validate --type porto_ids
	@echo "Validating graph.json..."
	@. $(VENV)/bin/activate && PYTHONPATH=. python -m cli.main validate --type graph

validate-graph: ensure-venv
	@echo "Validating graph.json consistency..."
	@. $(VENV)/bin/activate && PYTHONPATH=. python -m cli.main validate --type graph

format-json:
	@if [ -n "$(CHECK)" ]; then echo "Checking JSON formatting..."; else echo "Formatting JSON files..."; fi
	@for file in porto_data/*.json porto_data/schemas/*.json porto_data/policy/*.json porto_data/formats/*.json porto_data/providers/*/*.json porto_data/providers/*/prices/*.json; do \
		if [ -f "$$file" ]; then \
			if [ -n "$(CHECK)" ]; then \
				$(PYTHON3) scripts/format_json_file.py --check "$$file" && echo "✓ $$file (already formatted)" || (echo "✗ $$file is not properly formatted"; exit 1); \
			else \
				$(PYTHON3) scripts/format_json_file.py "$$file" && echo "✓ Formatted $$file" || (echo "✗ $$file: Invalid JSON - cannot format"; exit 1); \
			fi; \
		fi; \
	done
	@if [ -n "$(CHECK)" ]; then echo "✓ All JSON files are properly formatted"; else echo "✓ All JSON files formatted"; fi

lint-json:
	@echo "Linting JSON files for syntax errors..."
	@for file in porto_data/*.json porto_data/schemas/*.json porto_data/policy/*.json porto_data/formats/*.json porto_data/providers/*/*.json porto_data/providers/*/prices/*.json; do \
		if [ -f "$$file" ]; then \
			$(PYTHON3) -m json.tool "$$file" > /dev/null && echo "✓ $$file" || (echo "✗ $$file: JSON syntax error" && exit 1); \
		fi; \
	done
	@echo "✓ All JSON files are valid"

# ==========================================
# Code Commands
# ==========================================
format-code: ensure-venv
	@if [ -n "$(CHECK)" ]; then \
		echo "Checking Python code formatting..."; \
		. $(VENV)/bin/activate && ruff format --check . || (echo "✗ Code is not properly formatted. Run 'make format-code' to fix." && exit 1); \
		echo "✓ Code formatting check complete"; \
	else \
		echo "Formatting Python code..."; \
		. $(VENV)/bin/activate && ruff format . || (echo "✗ Failed to format code with ruff" && exit 1); \
		. $(VENV)/bin/activate && ruff check --fix . || (echo "✗ Failed to fix linting issues with ruff" && exit 1); \
		echo "✓ Code formatted"; \
	fi

lint-code: ensure-venv
	@echo "Linting Python code..."
	@. $(VENV)/bin/activate && ruff check . || (echo "✗ Code linting failed. Fix issues before committing." && exit 1)
	@echo "✓ Code linting complete"

type-check: ensure-venv
	@echo "Type checking Python code..."
	@. $(VENV)/bin/activate && PYTHONPATH=. mypy scripts/ cli/
	@echo "✓ Type check complete"

# ==========================================
# Testing
# ==========================================
test: ensure-venv
	@echo "Running tests..."
	@. $(VENV)/bin/activate && PYTHONPATH=. pytest
	@echo "✓ Tests complete"

test-cov: ensure-venv
	@echo "Running tests with coverage..."
	@. $(VENV)/bin/activate && PYTHONPATH=. pytest --cov-report=html --cov-report=xml
	@echo "✓ Coverage report complete (see htmlcov/index.html for detailed report)"

# ==========================================
# Metadata
# ==========================================
metadata: ensure-venv
	@. $(VENV)/bin/activate && PYTHONPATH=. python -m cli.main metadata

# ==========================================
# Hooks (internal — run from ensure-venv)
# ==========================================
install-hooks: ensure-venv
	@echo "Installing pre-commit hooks..."
	@if [ -f $(VENV)/bin/pre-commit ]; then \
		$(VENV)/bin/pre-commit install; \
	else \
		echo "Error: pre-commit not found."; \
		exit 1; \
	fi
	@echo "✓ Pre-commit hooks installed"

# ==========================================
# Quality
# ==========================================
quality: ensure-venv validate format lint type-check

# ==========================================
# Test before publish (npm + PyPI)
# ==========================================
test-publish: ensure-venv
	@./tests/test_publish.sh
