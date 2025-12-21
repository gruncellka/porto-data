#!/usr/bin/env python3
"""Tests for CLI metadata command."""

from unittest.mock import patch

from cli.commands.metadata import generate_metadata


class TestGenerateMetadata:
    """Test generate_metadata function."""

    @patch("cli.commands.metadata.generate_metadata_main")
    def test_generate_metadata_success(self, mock_gen):
        """Test successful metadata generation."""
        mock_gen.return_value = None

        result = generate_metadata()
        assert result == 0
        mock_gen.assert_called_once()

    @patch("cli.commands.metadata.generate_metadata_main")
    def test_generate_metadata_exception(self, mock_gen):
        """Test metadata generation with exception."""
        mock_gen.side_effect = Exception("Test error")

        result = generate_metadata()
        assert result == 1
