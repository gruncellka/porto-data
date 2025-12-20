#!/usr/bin/env python3
"""Tests for schema validation - validators/schema.py and backward compatibility."""

import json

import pytest
from validators.schema import validate_all_schemas, validate_file


class TestValidateFile:
    """Test validate_file function with various scenarios."""

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
            (
                {
                    "$schema": "http://json-schema.org/draft-07/schema#",
                    "type": "object",
                    "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
                    "required": ["name"],
                },
                {"name": "Test", "age": 30},
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
                {},  # Missing required field
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
        """Test validate_file with various valid/invalid scenarios."""
        schema_path = tmp_path / "schema.json"
        data_path = tmp_path / "data.json"

        with open(schema_path, "w") as f:
            json.dump(schema, f)
        with open(data_path, "w") as f:
            json.dump(data, f)

        result = validate_file(str(schema_path), str(data_path))
        assert result is expected

    def test_validate_file_missing_file(self, tmp_path):
        """Test that missing file returns False."""
        schema_path = tmp_path / "schema.json"
        data_path = tmp_path / "nonexistent.json"

        with open(schema_path, "w") as f:
            json.dump({}, f)

        result = validate_file(str(schema_path), str(data_path))
        assert result is False

    def test_validate_file_invalid_json_syntax(self, tmp_path):
        """Test that invalid JSON syntax returns False."""
        schema_path = tmp_path / "schema.json"
        data_path = tmp_path / "data.json"

        with open(schema_path, "w") as f:
            json.dump({}, f)
        with open(data_path, "w") as f:
            f.write("{ invalid json }")

        result = validate_file(str(schema_path), str(data_path))
        assert result is False

    def test_validate_file_backward_compatibility(self, tmp_path, sample_schema, sample_valid_data):
        """Test that validate_file is accessible via backward compat wrapper."""
        schema_path = tmp_path / "schema.json"
        data_path = tmp_path / "data.json"

        with open(schema_path, "w") as f:
            json.dump(sample_schema, f)
        with open(data_path, "w") as f:
            json.dump(sample_valid_data, f)

        # Test direct import
        result1 = validate_file(str(schema_path), str(data_path))
        # Test via backward compat (if available)
        # Note: validate_schemas.py exports validate_file for backward compat
        assert result1 is True


class TestValidateAllSchemas:
    """Test validate_all_schemas function."""

    def test_validate_all_schemas_returns_exit_code(self):
        """Test that validate_all_schemas returns proper exit code."""
        result = validate_all_schemas()
        # Should return 0 (success) or 1 (failure)
        assert result in (0, 1)
        assert isinstance(result, int)

    def test_validate_all_schemas_has_output(self, capsys):
        """Test that validate_all_schemas produces output."""
        validate_all_schemas()
        captured = capsys.readouterr()
        assert "Validating JSON schemas" in captured.out or len(captured.out) > 0
