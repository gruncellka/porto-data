.PHONY: help setup install-hooks
.PHONY: validate-json validate-data-links lint-json format-json format-code lint-code type-check
.PHONY: validate format lint metadata test test-cov

help:
	@echo "Porto Data - Schema Validation & Code Quality"
	@echo "=============================================="
	@echo ""
	@echo "Setup (First Time):"
	@echo "  make setup         - Install dependencies and pre-commit hooks"
	@echo ""
	@echo "Most Common Commands:"
	@echo "  make validate      - Validate all JSON files against schemas (most important)"
	@echo "  make format        - Format both JSON and Python code"
	@echo "  make lint          - Lint both JSON and Python code"
	@echo ""
	@echo "JSON Commands:"
	@echo "  make validate-json    - Validate all JSON files against schemas"
	@echo "  make validate-data-links - Validate data_links.json consistency with data files"
	@echo "  make format-json        - Format JSON files (use CHECK=1 for read-only check)"
	@echo "  make lint-json        - Check JSON files for syntax errors (read-only)"
	@echo ""
	@echo "Code Commands:"
	@echo "  make format-code        - Format Python code with ruff (use CHECK=1 for read-only check)"
	@echo "  make lint-code        - Lint Python code with ruff"
	@echo "  make type-check       - Type check Python code with mypy"
	@echo ""
	@echo "Testing:"
	@echo "  make test             - Run all tests"
	@echo "  make test-cov         - Run tests with coverage report"
	@echo ""
	@echo "Metadata:"
	@echo "  make metadata      - Generate metadata.json with checksums"
	@echo ""
	@echo "Hooks:"
	@echo "  make install-hooks - Install pre-commit hook (usually done by setup)"
	@echo ""

# ==========================================
# Setup (First Time)
# ==========================================
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

# ==========================================
# Most Common Commands
# ==========================================
validate: validate-json

format: format-json format-code

lint: lint-json lint-code

# ==========================================
# JSON Commands
# ==========================================
validate-json:
	@echo "Validating JSON against schemas..."
	@. venv/bin/activate && porto validate --type schema
	@echo "Validating data_links.json..."
	@. venv/bin/activate && porto validate --type links

validate-data-links:
	@echo "Validating data_links.json consistency..."
	@. venv/bin/activate && porto validate --type links

format-json:
	@if [ -n "$(CHECK)" ]; then echo "Checking JSON formatting..."; else echo "Formatting JSON files..."; fi
	@for file in porto_data/data/*.json porto_data/schemas/*.json; do \
		if [ -f "$$file" ]; then \
			if python3 -m json.tool "$$file" "$$file.tmp" > /dev/null 2>&1; then \
				if ! cmp -s "$$file" "$$file.tmp"; then \
					if [ -n "$(CHECK)" ]; then \
						echo "✗ $$file is not properly formatted"; \
						rm -f "$$file.tmp"; \
						exit 1; \
					fi; \
					if mv "$$file.tmp" "$$file"; then \
						echo "✓ Formatted $$file"; \
					else \
						echo "✗ $$file: Failed to move formatted file (permissions issue?)"; \
						rm -f "$$file.tmp"; \
						exit 1; \
					fi; \
				else \
					rm -f "$$file.tmp" && echo "✓ $$file (already formatted)"; \
				fi; \
			else \
				echo "✗ $$file: Invalid JSON - cannot format"; \
				rm -f "$$file.tmp"; \
				exit 1; \
			fi; \
		fi; \
	done
	@if [ -n "$(CHECK)" ]; then echo "✓ All JSON files are properly formatted"; else echo "✓ All JSON files formatted"; fi

lint-json:
	@echo "Linting JSON files for syntax errors..."
	@for file in porto_data/data/*.json; do \
		python3 -m json.tool "$$file" > /dev/null && echo "✓ $$file" || (echo "✗ $$file: JSON syntax error" && exit 1); \
	done
	@for file in porto_data/schemas/*.json; do \
		python3 -m json.tool "$$file" > /dev/null && echo "✓ $$file" || (echo "✗ $$file: JSON syntax error" && exit 1); \
	done
	@echo "✓ All JSON files are valid"

# ==========================================
# Code Commands
# ==========================================
format-code:
	@if [ -n "$(CHECK)" ]; then \
		echo "Checking Python code formatting..."; \
		. venv/bin/activate && ruff format --check . || (echo "✗ Code is not properly formatted. Run 'make format-code' to fix." && exit 1); \
		echo "✓ Code formatting check complete"; \
	else \
		echo "Formatting Python code..."; \
		. venv/bin/activate && ruff format . || (echo "✗ Failed to format code with ruff" && exit 1); \
		. venv/bin/activate && ruff check --fix . || (echo "✗ Failed to fix linting issues with ruff" && exit 1); \
		echo "✓ Code formatted"; \
	fi

lint-code:
	@echo "Linting Python code..."
	@. venv/bin/activate && ruff check . || (echo "✗ Code linting failed. Fix issues before committing." && exit 1)
	@echo "✓ Code linting complete"

type-check:
	@echo "Type checking Python code..."
	@. venv/bin/activate && PYTHONPATH=. mypy scripts/ cli/
	@echo "✓ Type check complete"

# ==========================================
# Testing
# ==========================================
test:
	@echo "Running tests..."
	@. venv/bin/activate && pytest tests/ -v
	@echo "✓ Tests complete"

test-cov:
	@echo "Running tests with coverage..."
	@. venv/bin/activate && pytest tests/ --cov=scripts --cov=cli --cov-report=term-missing --cov-report=html --cov-report=xml --cov-fail-under=80
	@echo "✓ Coverage report complete (see htmlcov/index.html for detailed report)"

# ==========================================
# Metadata
# ==========================================
metadata:
	@. venv/bin/activate && porto metadata

# Regenerate metadata after version change (runs automatically via pre-commit)
# But you can also run manually: make metadata

# ==========================================
# Hooks (Usually Automatic)
# ==========================================
install-hooks:
	@echo "Installing pre-commit hooks..."
	@if [ -f venv/bin/pre-commit ]; then \
		venv/bin/pre-commit install; \
	else \
		echo "Error: pre-commit not found. Run 'make setup' first."; \
		exit 1; \
	fi
	@echo "✓ Pre-commit hooks installed"
