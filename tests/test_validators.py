#!/usr/bin/env python3
"""Tests for validators - direct unit testing of validator classes and functions."""

import json

import pytest
from validators.base import ValidationResults
from validators.links import DataLinksValidator
from validators.schema import validate_all_schemas, validate_file


class TestValidationResults:
    """Test ValidationResults TypedDict structure."""

    def test_validation_results_structure(self):
        """Test that ValidationResults has correct structure."""
        results: ValidationResults = {
            "errors": [],
            "warnings": [],
            "fixes_needed": [],
            "correct": [],
        }

        assert isinstance(results["errors"], list)
        assert isinstance(results["warnings"], list)
        assert isinstance(results["fixes_needed"], list)
        assert isinstance(results["correct"], list)

    def test_validation_results_can_have_items(self):
        """Test that ValidationResults can contain items."""
        results: ValidationResults = {
            "errors": ["error1", "error2"],
            "warnings": ["warning1"],
            "fixes_needed": ["fix1"],
            "correct": ["correct1", "correct2"],
        }

        assert len(results["errors"]) == 2
        assert len(results["warnings"]) == 1
        assert len(results["fixes_needed"]) == 1
        assert len(results["correct"]) == 2


class TestSchemaValidator:
    """Test schema validator functions."""

    @pytest.mark.parametrize(
        "schema,data,expected",
        [
            # Valid cases
            (
                {
                    "$schema": "http://json-schema.org/draft-07/schema#",
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"],
                },
                {"name": "Test"},
                True,
            ),
            # Invalid cases
            (
                {
                    "$schema": "http://json-schema.org/draft-07/schema#",
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"],
                },
                {},  # Missing required
                False,
            ),
            (
                {
                    "$schema": "http://json-schema.org/draft-07/schema#",
                    "type": "object",
                    "properties": {"age": {"type": "integer"}},
                },
                {"age": "thirty"},  # Wrong type
                False,
            ),
        ],
    )
    def test_validate_file_scenarios(self, tmp_path, schema, data, expected):
        """Test validate_file with parametrized scenarios."""
        schema_path = tmp_path / "schema.json"
        data_path = tmp_path / "data.json"

        with open(schema_path, "w") as f:
            json.dump(schema, f)
        with open(data_path, "w") as f:
            json.dump(data, f)

        result = validate_file(str(schema_path), str(data_path))
        assert result is expected

    def test_validate_file_error_handling(self, tmp_path):
        """Test validate_file error handling."""
        schema_path = tmp_path / "schema.json"
        data_path = tmp_path / "nonexistent.json"

        with open(schema_path, "w") as f:
            json.dump({}, f)

        result = validate_file(str(schema_path), str(data_path))
        assert result is False

    def test_validate_all_schemas_returns_exit_code(self):
        """Test that validate_all_schemas returns proper exit code."""
        result = validate_all_schemas()
        assert result in (0, 1)
        assert isinstance(result, int)


class TestDataLinksValidatorUnit:
    """Unit tests for DataLinksValidator class methods."""

    def test_validator_initialization(self, minimal_data_files):
        """Test validator initialization."""
        validator = DataLinksValidator(minimal_data_files)
        assert validator.data_dir == minimal_data_files
        assert isinstance(validator.results, dict)
        assert all(
            key in validator.results for key in ["errors", "warnings", "fixes_needed", "correct"]
        )

    def test_validator_loads_data(self, minimal_data_files):
        """Test that validator loads data correctly."""
        validator = DataLinksValidator(minimal_data_files)
        validator.load_data()

        assert validator.data_links is not None
        assert validator.products is not None
        assert isinstance(validator.product_dict, dict)
        assert isinstance(validator.zone_ids, dict)
        assert isinstance(validator.weight_tier_ids, set)

    def test_validator_validate_all_structure(self, minimal_data_files):
        """Test that validate_all returns proper structure."""
        validator = DataLinksValidator(minimal_data_files)
        results = validator.validate_all()

        assert isinstance(results, dict)
        assert all(key in results for key in ["errors", "warnings", "fixes_needed", "correct"])
        assert all(isinstance(v, list) for v in results.values())

    def test_validator_handles_missing_files(self, tmp_path):
        """Test that validator handles missing data files gracefully."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        # Create only data_links.json
        with open(data_dir / "data_links.json", "w") as f:
            json.dump({"file_type": "data_links", "links": {}}, f)

        validator = DataLinksValidator(data_dir)
        results = validator.validate_all()

        # Should have errors about missing files
        assert len(results["errors"]) > 0
        assert any("Missing file" in e or "not found" in e.lower() for e in results["errors"])
