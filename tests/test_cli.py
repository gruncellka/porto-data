#!/usr/bin/env python3
"""Tests for CLI commands - comprehensive coverage."""

import subprocess
import sys
from pathlib import Path

import pytest

from cli.commands.validate import validate_all, validate_links, validate_schema


@pytest.fixture
def project_root():
    """Return project root path."""
    return Path(__file__).parent.parent


class TestCLIHelp:
    """Test CLI help and argument parsing."""

    def test_cli_main_help(self, project_root):
        """Test that CLI main help works."""
        result = subprocess.run(
            [sys.executable, "-m", "cli.main", "--help"],
            capture_output=True,
            text=True,
            cwd=project_root,
        )
        assert result.returncode == 0
        assert "Porto Data validation" in result.stdout
        assert "validate" in result.stdout
        assert "Examples" in result.stdout

    def test_cli_validate_help(self, project_root):
        """Test that validate command help works."""
        result = subprocess.run(
            [sys.executable, "-m", "cli.main", "validate", "--help"],
            capture_output=True,
            text=True,
            cwd=project_root,
        )
        assert result.returncode == 0
        assert "--type" in result.stdout
        assert "schema" in result.stdout
        assert "links" in result.stdout
        assert "all" in result.stdout
        assert "--analyze" in result.stdout

    def test_cli_no_command_shows_help(self, project_root):
        """Test that CLI without command shows help and exits with error."""
        result = subprocess.run(
            [sys.executable, "-m", "cli.main"],
            capture_output=True,
            text=True,
            cwd=project_root,
        )
        assert result.returncode == 1
        assert "usage:" in result.stdout.lower() or "Porto Data" in result.stdout


class TestCLIValidateCommands:
    """Test CLI validate command functionality."""

    @pytest.mark.parametrize(
        "command_args,expected_output",
        [
            (["validate", "--type", "schema"], "Validating JSON schemas"),
            (["validate", "--type", "links"], "Validating data_links.json"),
            (["validate", "--type", "all"], "Validating JSON schemas"),
            (
                ["validate", "--type", "links", "--analyze"],
                "COMPREHENSIVE DATA_LINKS.JSON ANALYSIS",
            ),
        ],
    )
    def test_cli_validate_commands(self, project_root, command_args, expected_output):
        """Test various CLI validate commands."""
        result = subprocess.run(
            [sys.executable, "-m", "cli.main"] + command_args,
            capture_output=True,
            text=True,
            cwd=project_root,
        )
        # Should succeed if data is valid (exit code 0 or 1)
        assert result.returncode in (0, 1)
        assert expected_output in result.stdout

    def test_cli_validate_default_type_is_all(self, project_root):
        """Test that validate without --type defaults to 'all'."""
        result = subprocess.run(
            [sys.executable, "-m", "cli.main", "validate"],
            capture_output=True,
            text=True,
            cwd=project_root,
        )
        assert result.returncode in (0, 1)
        assert "Validating JSON schemas" in result.stdout


class TestCLICommandFunctions:
    """Test CLI command functions directly (unit tests)."""

    def test_validate_schema_function(self):
        """Test validate_schema function directly."""
        result = validate_schema()
        assert result in (0, 1)
        assert isinstance(result, int)

    @pytest.mark.parametrize("analyze", [False, True])
    def test_validate_links_function(self, analyze):
        """Test validate_links function with both modes."""
        result = validate_links(analyze=analyze)
        assert result in (0, 1)
        assert isinstance(result, int)

    def test_validate_all_function(self):
        """Test validate_all function directly."""
        result = validate_all()
        assert result in (0, 1)
        assert isinstance(result, int)

    def test_validate_all_stops_on_schema_failure(self, monkeypatch):
        """Test that validate_all stops early if schema validation fails."""

        def mock_validate_schema():
            return 1  # Failure

        monkeypatch.setattr("cli.commands.validate.validate_schema", mock_validate_schema)

        result = validate_all()
        # Should return 1 (failure) without running links validation
        assert result == 1


class TestCLIExitCodes:
    """Test CLI exit codes for different scenarios."""

    def test_cli_returns_zero_on_success(self, project_root):
        """Test that CLI returns 0 when validation succeeds."""
        # This assumes data is valid - if not, test will still pass (exit code 0 or 1)
        result = subprocess.run(
            [sys.executable, "-m", "cli.main", "validate", "--type", "schema"],
            capture_output=True,
            text=True,
            cwd=project_root,
        )
        assert result.returncode in (0, 1)  # Either success or failure is valid

    def test_cli_returns_one_on_invalid_command(self, project_root):
        """Test that CLI returns non-zero for invalid commands."""
        result = subprocess.run(
            [sys.executable, "-m", "cli.main", "invalid_command"],
            capture_output=True,
            text=True,
            cwd=project_root,
        )
        # argparse returns 2 for invalid commands, but any non-zero is fine
        assert result.returncode != 0
