.PHONY: help setup install-hooks
.PHONY: validate-json lint-json format-json
.PHONY: format-code lint-code type-check
.PHONY: validate format lint quality metadata

help:
	@echo "Porto Data - Schema Validation & Code Quality"
	@echo "=============================================="
	@echo ""
	@echo "Setup:"
	@echo "  make setup         - Install dependencies and pre-commit hooks"
	@echo ""
	@echo "JSON Commands:"
	@echo "  make validate-json - Validate all JSON files against schemas"
	@echo "  make lint-json     - Check JSON files for syntax errors (read-only)"
	@echo "  make format-json   - Format and standardize JSON files (modifies files)"
	@echo ""
	@echo "Code Commands:"
	@echo "  make format-code   - Format Python code with ruff"
	@echo "  make lint-code     - Lint Python code with ruff"
	@echo "  make type-check    - Type check Python code with mypy"
	@echo ""
	@echo "Unified Commands:"
	@echo "  make validate      - Alias for validate-json"
	@echo "  make format        - Format both JSON and code"
	@echo "  make lint          - Lint both JSON and code"
	@echo "  make quality       - Run all quality checks"
	@echo ""
	@echo "Metadata:"
	@echo "  make metadata      - Generate metadata.json with checksums"
	@echo ""
	@echo "Hooks:"
	@echo "  make install-hooks - Install pre-commit hook"
	@echo ""

# JSON Commands
validate-json:
	@echo "Validating JSON against schemas..."
	@. venv/bin/activate && python3 scripts/validate_schemas.py

lint-json:
	@echo "Linting JSON files for syntax errors..."
	@for file in data/*.json; do \
		python3 -m json.tool "$$file" > /dev/null && echo "✓ $$file" || (echo "✗ $$file: JSON syntax error" && exit 1); \
	done
	@for file in schemas/*.json; do \
		python3 -m json.tool "$$file" > /dev/null && echo "✓ $$file" || (echo "✗ $$file: JSON syntax error" && exit 1); \
	done
	@echo "✓ All JSON files are valid"

format-json:
	@echo "Formatting JSON files..."
	@for file in data/*.json schemas/*.json; do \
		python3 -m json.tool "$$file" "$$file.tmp" && mv "$$file.tmp" "$$file" && echo "✓ $$file"; \
	done
	@echo "✓ All JSON files formatted"

# Code Commands
format-code:
	@echo "Formatting Python code..."
	@. venv/bin/activate && ruff format .
	@. venv/bin/activate && ruff check --fix .
	@echo "✓ Code formatted"

lint-code:
	@echo "Linting Python code..."
	@. venv/bin/activate && ruff check .
	@echo "✓ Code linting complete"

type-check:
	@echo "Type checking Python code..."
	@. venv/bin/activate && mypy scripts/
	@echo "✓ Type check complete"

# Unified Commands
validate: validate-json

format: format-json format-code

lint: lint-json lint-code

quality: format-json lint-json validate-json format-code lint-code type-check

metadata:
	@. venv/bin/activate && python3 scripts/generate_metadata.py

install-hooks:
	@echo "Installing pre-commit hooks..."
	@if [ -f venv/bin/pre-commit ]; then \
		venv/bin/pre-commit install; \
	else \
		echo "Error: pre-commit not found. Run 'make setup' first."; \
		exit 1; \
	fi
	@echo "✓ Pre-commit hooks installed"

setup:
	@echo "Setting up porto-data..."
	@python3 -m venv venv
	@. venv/bin/activate && pip install -q -e ".[dev]"
	@if [ -d .git ]; then \
		$(MAKE) install-hooks || echo "Warning: Could not install pre-commit hooks. Run 'make install-hooks' manually."; \
	else \
		echo "Skipping hook installation (not a git repository)"; \
	fi
	@echo "✓ Setup complete - run 'make help' for commands"
