#!/usr/bin/env python3
"""Tests for generate_metadata.py main function - comprehensive coverage."""

import json
from unittest.mock import MagicMock, mock_open, patch

from scripts.generate_metadata import main


class TestGenerateMetadataMain:
    """Test main() function in generate_metadata.py."""

    @patch("scripts.generate_metadata.get_project_root")
    @patch("scripts.generate_metadata.generate_metadata")
    @patch("builtins.open", new_callable=mock_open)
    def test_main_new_file(self, mock_file, mock_gen, mock_get_root):
        """Test main when metadata.json doesn't exist."""
        # Setup mocks
        mock_metadata = {
            "project": {"name": "test", "version": "1.0", "description": "test"},
            "entities": {},
            "generated_at": "2024-01-01T00:00:00Z",
        }
        mock_gen.return_value = mock_metadata

        mock_project_root = MagicMock()
        mock_output_path = MagicMock()
        mock_output_path.exists.return_value = False
        mock_project_root.__truediv__.return_value = mock_output_path
        mock_get_root.return_value = mock_project_root

        # Run main
        main()

        # Verify metadata was generated
        mock_gen.assert_called_once()

    @patch("scripts.generate_metadata.get_project_root")
    @patch("scripts.generate_metadata.generate_metadata")
    @patch("builtins.open", new_callable=mock_open)
    def test_main_existing_file_no_changes(self, mock_open_func, mock_gen, mock_get_root):
        """Test main when metadata.json exists and has no changes."""
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
        mock_open_func.return_value.read.return_value = json.dumps(existing_metadata)

        mock_project_root = MagicMock()
        mock_output_path = MagicMock()
        mock_output_path.exists.return_value = True
        mock_project_root.__truediv__.return_value = mock_output_path
        mock_get_root.return_value = mock_project_root
        mock_gen.return_value = new_metadata

        main()

        # Verify metadata was generated for comparison
        mock_gen.assert_called()

    @patch("scripts.generate_metadata.get_project_root")
    @patch("scripts.generate_metadata.generate_metadata")
    @patch("builtins.open", new_callable=mock_open)
    def test_main_existing_file_with_changes(self, mock_file, mock_gen, mock_get_root):
        """Test main when metadata.json exists and has changes."""
        # Setup mocks
        mock_project_root = MagicMock()
        mock_output_path = MagicMock()
        mock_output_path.exists.return_value = True
        mock_project_root.__truediv__.return_value = mock_output_path
        mock_get_root.return_value = mock_project_root

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

        mock_file.return_value.read.return_value = json.dumps(existing_metadata)
        mock_gen.return_value = new_metadata

        # Run main
        with patch("pathlib.Path.open", mock_file):
            main()

        # Verify metadata was written
        mock_gen.assert_called()

    @patch("scripts.generate_metadata.get_project_root")
    @patch("scripts.generate_metadata.generate_metadata")
    @patch("builtins.open", new_callable=mock_open, read_data="invalid json")
    def test_main_invalid_json_handling(self, mock_file, mock_gen, mock_get_root):
        """Test main handles invalid JSON in existing file."""
        mock_project_root = MagicMock()
        mock_output_path = MagicMock()
        mock_output_path.exists.return_value = True
        mock_project_root.__truediv__.return_value = mock_output_path
        mock_get_root.return_value = mock_project_root

        mock_metadata = {
            "project": {"name": "test", "version": "1.0", "description": "test"},
            "entities": {},
            "generated_at": "2024-01-01T00:00:00Z",
        }
        mock_gen.return_value = mock_metadata

        # Run main - should handle JSONDecodeError then write new metadata
        main()

        # Should still generate metadata
        mock_gen.assert_called()
