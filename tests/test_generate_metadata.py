#!/usr/bin/env python3
"""Tests for generate_metadata.py"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from generate_metadata import (
    extract_entity_name,
    generate_metadata,
    get_file_info,
    get_project_metadata,
    get_schema_url,
)


class TestExtractEntityName:
    """Test extract_entity_name function."""

    def test_extract_entity_name_from_data_file(self):
        """Test extracting entity name from data file."""
        path = Path("data/products.json")
        assert extract_entity_name(path) == "products"

    def test_extract_entity_name_from_schema_file(self):
        """Test extracting entity name from schema file."""
        path = Path("schemas/products.schema.json")
        assert extract_entity_name(path) == "products"

    def test_extract_entity_name_removes_schema_suffix(self):
        """Test that .schema suffix is removed."""
        path = Path("schemas/test.schema.json")
        assert extract_entity_name(path) == "test"


class TestGetFileInfo:
    """Test get_file_info function."""

    def test_get_file_info(self, tmp_path):
        """Test getting file info with checksum."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")
        base_path = tmp_path
        checksums = {"test.txt": "abc123"}

        info = get_file_info(test_file, base_path, checksums)

        assert info["path"] == "test.txt"
        assert info["checksum"] == "abc123"
        assert info["size"] == test_file.stat().st_size

    def test_get_file_info_uses_posix_path(self, tmp_path):
        """Test that paths use forward slashes (POSIX format)."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        test_file = subdir / "test.txt"
        test_file.write_text("content")
        base_path = tmp_path
        checksums = {}

        info = get_file_info(test_file, base_path, checksums)

        # Should use forward slashes even on Windows
        assert "/" in info["path"] or info["path"] == "subdir/test.txt"
        assert "\\" not in info["path"]


class TestGetSchemaUrl:
    """Test get_schema_url function."""

    def test_get_schema_url_with_id(self, tmp_path):
        """Test extracting $id from schema file."""
        schema_file = tmp_path / "schema.json"
        schema_data = {
            "$id": "https://example.com/schema.json",
            "type": "object",
        }
        with open(schema_file, "w") as f:
            json.dump(schema_data, f)

        url = get_schema_url(schema_file)
        assert url == "https://example.com/schema.json"

    def test_get_schema_url_without_id(self, tmp_path):
        """Test that empty string is returned when $id is missing."""
        schema_file = tmp_path / "schema.json"
        schema_data = {"type": "object"}
        with open(schema_file, "w") as f:
            json.dump(schema_data, f)

        url = get_schema_url(schema_file)
        assert url == ""

    def test_get_schema_url_invalid_json(self, tmp_path):
        """Test that empty string is returned for invalid JSON."""
        schema_file = tmp_path / "schema.json"
        schema_file.write_text("{ invalid json }")

        url = get_schema_url(schema_file)
        assert url == ""

    def test_get_schema_url_missing_file(self, tmp_path):
        """Test that empty string is returned for missing file."""
        url = get_schema_url(tmp_path / "nonexistent.json")
        assert url == ""


class TestGetProjectMetadata:
    """Test get_project_metadata function."""

    def test_get_project_metadata(self, tmp_path):
        """Test extracting project metadata from pyproject.toml."""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_content = """
[project]
name = "test-project"
version = "1.0.0"
description = "Test description"
"""
        pyproject_file.write_text(pyproject_content)

        metadata = get_project_metadata(pyproject_file)

        assert metadata["name"] == "test-project"
        assert metadata["version"] == "1.0.0"
        assert metadata["description"] == "Test description"

    def test_get_project_metadata_missing_fields(self, tmp_path):
        """Test that defaults are used for missing fields."""
        pyproject_file = tmp_path / "pyproject.toml"
        pyproject_content = """
[project]
name = "test-project"
"""
        pyproject_file.write_text(pyproject_content)

        metadata = get_project_metadata(pyproject_file)

        assert metadata["name"] == "test-project"
        assert metadata["version"] == "0.0.0"  # Default
        assert metadata["description"] == ""  # Default


class TestGenerateMetadata:
    """Test generate_metadata function."""

    @patch("generate_metadata.get_all_file_checksums")
    @patch("generate_metadata.get_schema_data_mappings")
    @patch("generate_metadata.get_project_metadata")
    @patch("generate_metadata.Path.exists")
    @patch("generate_metadata.Path.stat")
    def test_generate_metadata_structure(
        self, mock_stat, mock_exists, mock_project_meta, mock_mappings, mock_checksums
    ):
        """Test that generate_metadata returns correct structure."""
        # Setup mocks
        mock_project_meta.return_value = {
            "name": "test-project",
            "version": "1.0.0",
            "description": "Test",
        }
        mock_mappings.return_value = {"schemas/products.schema.json": "data/products.json"}
        mock_checksums.return_value = {
            "schemas/products.schema.json": "schema_checksum",
            "data/products.json": "data_checksum",
        }
        mock_exists.return_value = True
        mock_stat.return_value.st_size = 100

        # Mock Path operations
        with patch("generate_metadata.Path") as mock_path:
            mock_schema_path = MagicMock()
            mock_data_path = MagicMock()
            mock_schema_path.exists.return_value = True
            mock_data_path.exists.return_value = True
            mock_schema_path.stem = "products.schema"
            mock_data_path.stem = "products"
            mock_path.side_effect = lambda p: (
                mock_schema_path if "schema" in str(p) else mock_data_path
            )

            # Mock get_schema_url
            with patch(
                "generate_metadata.get_schema_url", return_value="https://example.com/schema.json"
            ):
                metadata = generate_metadata()

        assert "project" in metadata
        assert "entities" in metadata
        assert "generated_at" in metadata
        assert "checksums" in metadata
        assert metadata["project"]["name"] == "test-project"
        assert metadata["project"]["version"] == "1.0.0"

    @patch("generate_metadata.get_all_file_checksums")
    @patch("generate_metadata.get_schema_data_mappings")
    @patch("generate_metadata.get_project_metadata")
    def test_generate_metadata_includes_entities(
        self, mock_project_meta, mock_mappings, mock_checksums
    ):
        """Test that entities are included in metadata."""
        mock_project_meta.return_value = {
            "name": "test",
            "version": "1.0.0",
            "description": "",
        }
        mock_mappings.return_value = {}
        mock_checksums.return_value = {}

        metadata = generate_metadata()

        assert "entities" in metadata
        assert isinstance(metadata["entities"], dict)

    def test_generate_metadata_has_timestamp(self):
        """Test that generated_at timestamp is included."""
        metadata = generate_metadata()

        assert "generated_at" in metadata
        assert isinstance(metadata["generated_at"], str)
        # Should be ISO format with Z suffix
        assert metadata["generated_at"].endswith("Z") or "+" in metadata["generated_at"]
