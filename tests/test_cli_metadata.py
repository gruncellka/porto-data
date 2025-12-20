#!/usr/bin/env python3
"""Tests for CLI metadata command - comprehensive coverage."""

from unittest.mock import MagicMock, patch

from cli.commands.metadata import (
    check_data_files_staged,
    check_metadata_status,
    generate_metadata,
    handle_metadata_generation,
)


class TestCheckMetadataStatus:
    """Test check_metadata_status function."""

    @patch("cli.commands.metadata.subprocess.run")
    def test_check_metadata_status_modified_and_staged(self, mock_run):
        """Test when metadata is both modified and staged."""
        # Mock modified check
        mock_modified = MagicMock()
        mock_modified.stdout = "metadata.json\n"
        # Mock staged check
        mock_staged = MagicMock()
        mock_staged.stdout = "metadata.json\n"

        mock_run.side_effect = [mock_modified, mock_staged]

        modified, staged = check_metadata_status()
        assert modified is True
        assert staged is True

    @patch("cli.commands.metadata.subprocess.run")
    def test_check_metadata_status_not_modified(self, mock_run):
        """Test when metadata is not modified."""
        mock_modified = MagicMock()
        mock_modified.stdout = ""
        mock_staged = MagicMock()
        mock_staged.stdout = ""

        mock_run.side_effect = [mock_modified, mock_staged]

        modified, staged = check_metadata_status()
        assert modified is False
        assert staged is False


class TestCheckDataFilesStaged:
    """Test check_data_files_staged function."""

    @patch("cli.commands.metadata.subprocess.run")
    def test_check_data_files_staged_true(self, mock_run):
        """Test when data files are staged."""
        mock_result = MagicMock()
        mock_result.stdout = "data/products.json\n"
        mock_run.return_value = mock_result

        result = check_data_files_staged()
        assert result is True

    @patch("cli.commands.metadata.subprocess.run")
    def test_check_data_files_staged_false(self, mock_run):
        """Test when no data files are staged."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        result = check_data_files_staged()
        assert result is False


class TestHandleMetadataGeneration:
    """Test handle_metadata_generation function."""

    @patch("cli.commands.metadata.has_file_changes")
    @patch("cli.commands.metadata.generate_metadata_main")
    @patch("cli.commands.metadata.check_metadata_status")
    @patch("cli.commands.metadata.check_data_files_staged")
    def test_handle_metadata_generation_with_changes_staged(
        self, mock_check_staged, mock_check_status, mock_gen, mock_has_changes
    ):
        """Test when changes detected and metadata is staged."""
        mock_has_changes.return_value = True
        mock_check_staged.return_value = True
        mock_check_status.return_value = (True, True)  # modified, staged
        mock_gen.return_value = None

        result = handle_metadata_generation()
        assert result == 0
        mock_gen.assert_called_once()

    @patch("cli.commands.metadata.has_file_changes")
    @patch("cli.commands.metadata.generate_metadata_main")
    @patch("cli.commands.metadata.check_metadata_status")
    @patch("cli.commands.metadata.check_data_files_staged")
    def test_handle_metadata_generation_error_not_staged(
        self, mock_check_staged, mock_check_status, mock_gen, mock_has_changes
    ):
        """Test error when data files staged but metadata not staged."""
        mock_has_changes.return_value = True
        mock_check_staged.return_value = True
        mock_check_status.return_value = (True, False)  # modified, not staged
        mock_gen.return_value = None

        result = handle_metadata_generation()
        assert result == 1

    @patch("cli.commands.metadata.has_file_changes")
    @patch("cli.commands.metadata.generate_metadata_main")
    @patch("cli.commands.metadata.check_metadata_status")
    @patch("cli.commands.metadata.check_data_files_staged")
    def test_handle_metadata_generation_no_changes(
        self, mock_check_staged, mock_check_status, mock_gen, mock_has_changes
    ):
        """Test when no changes detected."""
        mock_has_changes.return_value = False
        mock_check_staged.return_value = False
        mock_check_status.return_value = (False, False)

        result = handle_metadata_generation()
        assert result == 0
        mock_gen.assert_not_called()

    @patch("cli.commands.metadata.has_file_changes")
    @patch("cli.commands.metadata.generate_metadata_main")
    @patch("cli.commands.metadata.check_metadata_status")
    @patch("cli.commands.metadata.check_data_files_staged")
    def test_handle_metadata_generation_exception(
        self, mock_check_staged, mock_check_status, mock_gen, mock_has_changes
    ):
        """Test exception handling during generation."""
        mock_has_changes.return_value = True
        mock_check_staged.return_value = False
        mock_gen.side_effect = Exception("Test error")

        result = handle_metadata_generation()
        assert result == 0  # Returns 0 even on exception (just warns)

    @patch("cli.commands.metadata.has_file_changes")
    @patch("cli.commands.metadata.check_metadata_status")
    @patch("cli.commands.metadata.check_data_files_staged")
    def test_handle_metadata_generation_no_changes_but_staged_data(
        self, mock_check_staged, mock_check_status, mock_has_changes
    ):
        """Test when no changes but data files are staged and metadata modified."""
        mock_has_changes.return_value = False
        mock_check_staged.return_value = True
        mock_check_status.return_value = (True, False)  # modified, not staged

        result = handle_metadata_generation()
        assert result == 1


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
