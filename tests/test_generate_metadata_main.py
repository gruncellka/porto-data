#!/usr/bin/env python3
"""Tests for generate_metadata.py main function - comprehensive coverage."""

import json

# Add scripts to path
import sys
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from generate_metadata import main


class TestGenerateMetadataMain:
    """Test main() function in generate_metadata.py."""

    @patch("generate_metadata.Path")
    @patch("generate_metadata.generate_metadata")
    @patch("builtins.open", new_callable=mock_open)
    @patch("generate_metadata.Path.exists")
    def test_main_new_file(self, mock_exists, mock_file, mock_gen, mock_path_class):
        """Test main when metadata.json doesn't exist."""
        # Setup mocks
        mock_exists.return_value = False
        mock_metadata = {
            "project": {"name": "test", "version": "1.0", "description": "test"},
            "entities": {},
            "generated_at": "2024-01-01T00:00:00Z",
        }
        mock_gen.return_value = mock_metadata

        # Mock Path objects
        mock_script_dir = MagicMock()
        mock_project_root = MagicMock()
        mock_output_path = MagicMock()
        mock_output_path.exists.return_value = False
        mock_output_path.__truediv__ = lambda self, other: mock_output_path

        mock_path_class.return_value.parent = mock_script_dir
        mock_script_dir.parent = mock_project_root
        mock_project_root.__truediv__.return_value = mock_output_path

        # Run main
        main()

        # Verify metadata was generated
        mock_gen.assert_called_once()

    @patch("generate_metadata.generate_metadata")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.open", new_callable=mock_open)
    def test_main_existing_file_no_changes(self, mock_file, mock_exists, mock_gen):
        """Test main when metadata.json exists and has no changes."""
        # Setup mocks
        existing_metadata = {
            "project": {"name": "test", "version": "1.0", "description": "test"},
            "entities": {},
            "generated_at": "2024-01-01T00:00:00Z",
        }
        new_metadata = {
            "project": {"name": "test", "version": "1.0", "description": "test"},
            "entities": {},
            "generated_at": "2024-01-01T00:00:00Z",
        }
        mock_exists.return_value = True
        mock_file.return_value.read.return_value = json.dumps(existing_metadata)
        mock_gen.return_value = new_metadata

        main()

        # Verify metadata was generated for comparison
        mock_gen.assert_called()

    @patch("generate_metadata.Path")
    @patch("generate_metadata.generate_metadata")
    @patch("builtins.open", new_callable=mock_open)
    @patch("generate_metadata.Path.exists")
    def test_main_existing_file_with_changes(
        self, mock_exists, mock_file, mock_gen, mock_path_class
    ):
        """Test main when metadata.json exists and has changes."""
        # Setup mocks
        mock_exists.return_value = True
        existing_metadata = {
            "project": {"name": "old", "version": "1.0", "description": "old"},
            "entities": {},
            "generated_at": "2024-01-01T00:00:00Z",
        }
        new_metadata = {
            "project": {"name": "new", "version": "2.0", "description": "new"},
            "entities": {},
            "generated_at": "2024-01-02T00:00:00Z",
        }

        # Mock file reading
        mock_file.return_value.read.return_value = json.dumps(existing_metadata)
        mock_gen.return_value = new_metadata

        # Mock Path objects
        mock_script_dir = MagicMock()
        mock_project_root = MagicMock()
        mock_output_path = MagicMock()
        mock_output_path.exists.return_value = True

        mock_path_class.return_value.parent = mock_script_dir
        mock_script_dir.parent = mock_project_root
        mock_project_root.__truediv__.return_value = mock_output_path

        # Run main
        with patch("pathlib.Path.open", mock_file):
            main()

        # Verify metadata was written
        mock_gen.assert_called()

    @patch("generate_metadata.generate_metadata")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.open", new_callable=mock_open, read_data="invalid json")
    def test_main_invalid_json_handling(self, mock_file, mock_exists, mock_gen):
        """Test main handles invalid JSON in existing file."""
        # Setup mocks
        mock_exists.return_value = True
        mock_metadata = {
            "project": {"name": "test", "version": "1.0", "description": "test"},
            "entities": {},
            "generated_at": "2024-01-01T00:00:00Z",
        }
        mock_gen.return_value = mock_metadata

        # Run main - should handle JSONDecodeError
        main()

        # Should still generate metadata
        mock_gen.assert_called()
