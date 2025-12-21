#!/usr/bin/env python3
"""Tests for utils.py"""

import hashlib
import json
import sys
from pathlib import Path

import pytest

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from data_files import (
    get_data_file_path,
    get_data_files,
    get_schema_data_mappings,
    load_mappings,
)

from utils import (
    compute_checksum,
    get_all_file_checksums,
    get_existing_checksums_from_metadata,
    has_file_changes,
    load_json,
)


class TestLoadMappings:
    """Test load_mappings function."""

    def test_load_mappings_with_valid_file(self, tmp_path):
        """Test loading valid mappings.json."""
        mappings_file = tmp_path / "mappings.json"
        mappings_data = {
            "mappings": {
                "schemas/products.schema.json": "data/products.json",
                "schemas/services.schema.json": "data/services.json",
            }
        }
        with open(mappings_file, "w") as f:
            json.dump(mappings_data, f)

        result = load_mappings(str(mappings_file))
        assert result == mappings_data["mappings"]
        assert len(result) == 2

    def test_load_mappings_file_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised when mappings.json doesn't exist."""
        with pytest.raises(FileNotFoundError):
            load_mappings(str(tmp_path / "nonexistent.json"))

    def test_load_mappings_invalid_json(self, tmp_path):
        """Test that ValueError is raised for invalid JSON."""
        mappings_file = tmp_path / "mappings.json"
        with open(mappings_file, "w") as f:
            f.write("{ invalid json }")

        with pytest.raises(ValueError, match="Invalid JSON"):
            load_mappings(str(mappings_file))

    def test_load_mappings_no_mappings_key(self, tmp_path):
        """Test that ValueError is raised when mappings key is missing."""
        mappings_file = tmp_path / "mappings.json"
        with open(mappings_file, "w") as f:
            json.dump({}, f)

        with pytest.raises(ValueError, match="No mappings found"):
            load_mappings(str(mappings_file))

    def test_load_mappings_non_string_values(self, tmp_path):
        """Test that ValueError is raised for non-string mapping values."""
        mappings_file = tmp_path / "mappings.json"
        mappings_data = {
            "mappings": {
                "schemas/products.schema.json": 123,  # Should be string
            }
        }
        with open(mappings_file, "w") as f:
            json.dump(mappings_data, f)

        with pytest.raises(ValueError, match="must be strings"):
            load_mappings(str(mappings_file))


class TestComputeChecksum:
    """Test compute_checksum function."""

    def test_compute_checksum(self, tmp_path):
        """Test checksum computation."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        checksum = compute_checksum(str(test_file))

        # Verify it's a valid SHA256 hex digest
        assert len(checksum) == 64
        assert all(c in "0123456789abcdef" for c in checksum)

        # Verify it matches expected hash
        expected = hashlib.sha256(b"test content").hexdigest()
        assert checksum == expected

    def test_compute_checksum_different_content_different_hash(self, tmp_path):
        """Test that different content produces different checksums."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("content 1")
        file2.write_text("content 2")

        checksum1 = compute_checksum(str(file1))
        checksum2 = compute_checksum(str(file2))

        assert checksum1 != checksum2


class TestLoadJson:
    """Test load_json function."""

    def test_load_json_valid_file(self, tmp_path):
        """Test loading valid JSON file."""
        json_file = tmp_path / "test.json"
        data = {"key": "value", "number": 42}
        with open(json_file, "w") as f:
            json.dump(data, f)

        result = load_json(json_file)
        assert result == data

    def test_load_json_with_string_path(self, tmp_path):
        """Test loading JSON with string path."""
        json_file = tmp_path / "test.json"
        data = {"key": "value"}
        with open(json_file, "w") as f:
            json.dump(data, f)

        result = load_json(str(json_file))
        assert result == data

    def test_load_json_file_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised for missing file."""
        with pytest.raises(FileNotFoundError):
            load_json(tmp_path / "nonexistent.json")

    def test_load_json_invalid_json(self, tmp_path):
        """Test that JSONDecodeError is raised for invalid JSON."""
        json_file = tmp_path / "invalid.json"
        json_file.write_text("{ invalid json }")

        with pytest.raises(json.JSONDecodeError):
            load_json(json_file)


class TestGetDataFiles:
    """Test get_data_files function."""

    def test_get_data_files_returns_set(self):
        """Test that get_data_files returns a set of filenames."""
        data_files = get_data_files()

        assert isinstance(data_files, set)
        assert all(isinstance(f, str) for f in data_files)
        assert all(f.endswith(".json") for f in data_files)

    def test_get_data_files_includes_expected_files(self):
        """Test that expected data files are included."""
        data_files = get_data_files()

        # Should include common data files
        assert "products.json" in data_files or "services.json" in data_files


class TestGetSchemaDataMappings:
    """Test get_schema_data_mappings function."""

    def test_get_schema_data_mappings_returns_dict(self):
        """Test that mappings are returned as dictionary."""
        mappings = get_schema_data_mappings()

        assert isinstance(mappings, dict)
        assert len(mappings) > 0

    def test_get_schema_data_mappings_has_valid_structure(self):
        """Test that mappings have correct structure."""
        mappings = get_schema_data_mappings()

        for schema_path, data_path in mappings.items():
            assert isinstance(schema_path, str)
            assert isinstance(data_path, str)
            assert schema_path.endswith(".schema.json")
            assert data_path.endswith(".json")


class TestGetDataFilePath:
    """Test get_data_file_path function."""

    def test_get_data_file_path_valid_entity(self):
        """Test getting path for valid entity."""
        # This will use the actual project mappings
        try:
            path = get_data_file_path("products")
            assert isinstance(path, Path)
            assert path.name == "products.json"
        except FileNotFoundError:
            # If products doesn't exist in mappings, try another
            pytest.skip("products entity not in mappings")

    def test_get_data_file_path_invalid_entity(self):
        """Test that FileNotFoundError is raised for invalid entity."""
        with pytest.raises(FileNotFoundError, match="No mapping found"):
            get_data_file_path("nonexistent_entity")


class TestGetExistingChecksumsFromMetadata:
    """Test get_existing_checksums_from_metadata function."""

    def test_get_existing_checksums_from_metadata_new_structure(self, tmp_path):
        """Test extracting checksums from new metadata structure."""
        metadata_file = tmp_path / "metadata.json"
        metadata = {
            "entities": {
                "products": {
                    "data": {"path": "data/products.json", "checksum": "abc123"},
                    "schema": {"path": "schemas/products.schema.json", "checksum": "def456"},
                }
            }
        }
        with open(metadata_file, "w") as f:
            json.dump(metadata, f)

        checksums = get_existing_checksums_from_metadata(str(metadata_file))

        assert checksums["data/products.json"] == "abc123"
        assert checksums["schemas/products.schema.json"] == "def456"

    def test_get_existing_checksums_from_metadata_old_structure(self, tmp_path):
        """Test extracting checksums from old metadata structure."""
        metadata_file = tmp_path / "metadata.json"
        metadata = {
            "schemas": {"files": [{"path": "schemas/products.schema.json", "checksum": "abc123"}]},
            "data": {"files": [{"path": "data/products.json", "checksum": "def456"}]},
        }
        with open(metadata_file, "w") as f:
            json.dump(metadata, f)

        checksums = get_existing_checksums_from_metadata(str(metadata_file))

        assert checksums["schemas/products.schema.json"] == "abc123"
        assert checksums["data/products.json"] == "def456"

    def test_get_existing_checksums_from_metadata_missing_file(self, tmp_path):
        """Test that empty dict is returned when metadata file doesn't exist."""
        checksums = get_existing_checksums_from_metadata(str(tmp_path / "nonexistent.json"))
        assert checksums == {}

    def test_get_existing_checksums_from_metadata_invalid_json(self, tmp_path):
        """Test that empty dict is returned for invalid JSON."""
        metadata_file = tmp_path / "metadata.json"
        metadata_file.write_text("{ invalid json }")

        checksums = get_existing_checksums_from_metadata(str(metadata_file))
        assert checksums == {}


class TestHasFileChanges:
    """Test has_file_changes function."""

    def test_has_file_changes_with_changes(self, tmp_path, monkeypatch):
        """Test that has_file_changes detects changes in data or schema files."""

        # Mock the functions to return different checksums
        def mock_get_all_checksums():
            return {
                "data/products.json": "new_checksum",
                "schemas/products.schema.json": "schema_checksum",
            }

        def mock_get_existing_checksums():
            return {
                "data/products.json": "old_checksum",
                "schemas/products.schema.json": "schema_checksum",
            }

        monkeypatch.setattr("utils.get_all_file_checksums", mock_get_all_checksums)
        monkeypatch.setattr(
            "utils.get_existing_checksums_from_metadata", mock_get_existing_checksums
        )

        assert has_file_changes() is True

    def test_has_file_changes_no_changes(self, tmp_path, monkeypatch):
        """Test that has_file_changes returns False when no changes."""

        # Mock the functions to return same checksums
        def mock_get_all_checksums():
            return {
                "data/products.json": "same_checksum",
                "schemas/products.schema.json": "schema_checksum",
            }

        def mock_get_existing_checksums():
            return {
                "data/products.json": "same_checksum",
                "schemas/products.schema.json": "schema_checksum",
            }

        monkeypatch.setattr("utils.get_all_file_checksums", mock_get_all_checksums)
        monkeypatch.setattr(
            "utils.get_existing_checksums_from_metadata", mock_get_existing_checksums
        )

        assert has_file_changes() is False

    def test_has_file_changes_schema_changed(self, tmp_path, monkeypatch):
        """Test that has_file_changes detects schema file changes."""

        # Mock the functions - schema changed, data unchanged
        def mock_get_all_checksums():
            return {
                "data/products.json": "same_checksum",
                "schemas/products.schema.json": "new_schema_checksum",
            }

        def mock_get_existing_checksums():
            return {
                "data/products.json": "same_checksum",
                "schemas/products.schema.json": "old_schema_checksum",
            }

        monkeypatch.setattr("utils.get_all_file_checksums", mock_get_all_checksums)
        monkeypatch.setattr(
            "utils.get_existing_checksums_from_metadata", mock_get_existing_checksums
        )

        assert has_file_changes() is True


class TestGetAllFileChecksums:
    """Test get_all_file_checksums function."""

    def test_get_all_file_checksums_returns_dict(self):
        """Test that checksums are returned as dictionary."""
        checksums = get_all_file_checksums()

        assert isinstance(checksums, dict)
        # Should have some checksums if mappings exist
        if len(get_schema_data_mappings()) > 0:
            assert len(checksums) > 0

    def test_get_all_file_checksums_has_valid_checksums(self):
        """Test that returned checksums are valid SHA256 hashes."""
        checksums = get_all_file_checksums()

        for path, checksum in checksums.items():
            assert isinstance(path, str)
            assert isinstance(checksum, str)
            assert len(checksum) == 64  # SHA256 hex digest length
            assert all(c in "0123456789abcdef" for c in checksum)
