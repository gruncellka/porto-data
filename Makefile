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
	@python3 scripts/validate_schemas.py

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
	@ruff format .
	@ruff check --fix .
	@echo "✓ Code formatted"

lint-code:
	@echo "Linting Python code..."
	@ruff check .
	@echo "✓ Code linting complete"

type-check:
	@echo "Type checking Python code..."
	@mypy scripts/
	@echo "✓ Type check complete"

# Unified Commands
validate: validate-json

format: format-json format-code

lint: lint-json lint-code

quality: format-json lint-json validate-json format-code lint-code type-check

metadata:
	@python3 scripts/generate_metadata.py

install-hooks:
	@echo "Installing pre-commit hook..."
	@mkdir -p .git/hooks
	@cp hooks/pre-commit .git/hooks/pre-commit
	@chmod +x .git/hooks/pre-commit
	@echo "✓ Pre-commit hook installed"

setup:
	@echo "Setting up porto-data..."
	@pip install -q -e ".[dev]"
	@$(MAKE) install-hooks
	@echo "✓ Setup complete - run 'make help' for commands"
