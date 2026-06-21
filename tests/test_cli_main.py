#!/usr/bin/env python3
"""Tests for CLI main module - comprehensive coverage."""

import os
import runpy
import subprocess
import sys
from unittest.mock import MagicMock, patch

from cli.main import create_parser, main


class TestCreateParser:
    """Test parser creation."""

    def test_create_parser_returns_argparse_parser(self):
        """Test that create_parser returns an ArgumentParser."""
        parser = create_parser()
        assert parser is not None
        assert parser.prog == "porto"

    def test_create_parser_has_validate_subcommand(self):
        """Test that parser has validate subcommand."""
        parser = create_parser()
        # Parse with validate command
        args = parser.parse_args(["validate", "--type", "schema"])
        assert args.command == "validate"
        assert args.type == "schema"

    def test_create_parser_has_metadata_subcommand(self):
        """Test that parser has metadata subcommand."""
        parser = create_parser()
        args = parser.parse_args(["metadata"])
        assert args.command == "metadata"

    def test_create_parser_validate_has_analyze_flag(self):
        """Test that validate command has --analyze flag."""
        parser = create_parser()
        args = parser.parse_args(["validate", "--type", "graph", "--analyze"])
        assert args.analyze is True

    def test_create_parser_validate_default_type_is_none(self):
        """Test that validate with no --type has type None (run all)."""
        parser = create_parser()
        args = parser.parse_args(["validate"])
        assert args.type is None


class TestMainFunction:
    """Test main function with all code paths."""

    @patch("cli.commands.validate.validate_schema")
    def test_main_validate_schema(self, mock_validate_schema):
        """Test main with validate --type schema."""
        mock_validate_schema.return_value = 0
        with patch("sys.argv", ["porto", "validate", "--type", "schema"]):
            result = main()
            assert result == 0
            mock_validate_schema.assert_called_once()

    @patch("cli.commands.validate.validate_graph")
    def test_main_validate_graph(self, mock_validate_graph):
        """Test main with validate --type graph."""
        mock_validate_graph.return_value = 0
        with patch("sys.argv", ["porto", "validate", "--type", "graph"]):
            result = main()
            assert result == 0
            mock_validate_graph.assert_called_once_with(analyze=False)

    @patch("cli.commands.validate.validate_graph")
    def test_main_validate_graph_with_analyze(self, mock_validate_graph):
        """Test main with validate --type graph --analyze."""
        mock_validate_graph.return_value = 0
        with patch("sys.argv", ["porto", "validate", "--type", "graph", "--analyze"]):
            result = main()
            assert result == 0
            mock_validate_graph.assert_called_once_with(analyze=True)

    @patch("cli.commands.validate.validate_mappings")
    def test_main_validate_mappings(self, mock_validate_mappings):
        """Test main with validate --type mappings."""
        mock_validate_mappings.return_value = 0
        with patch("sys.argv", ["porto", "validate", "--type", "mappings"]):
            result = main()
            assert result == 0
            mock_validate_mappings.assert_called_once()

    @patch("cli.commands.validate.validate_limits")
    def test_main_validate_limits(self, mock_validate_limits):
        """Test main with validate --type limits."""
        mock_validate_limits.return_value = 0
        with patch("sys.argv", ["porto", "validate", "--type", "limits"]):
            result = main()
            assert result == 0
            mock_validate_limits.assert_called_once()

    @patch("cli.commands.validate.validate_all")
    def test_main_validate_all(self, mock_validate_all):
        """Test main with validate and no --type runs all."""
        mock_validate_all.return_value = 0
        with patch("sys.argv", ["porto", "validate"]):
            result = main()
            assert result == 0
            mock_validate_all.assert_called_once()

    @patch("cli.commands.validate.validate_all")
    def test_main_validate_default(self, mock_validate_all):
        """Test main with validate (defaults to all)."""
        mock_validate_all.return_value = 0
        with patch("sys.argv", ["porto", "validate"]):
            result = main()
            assert result == 0
            mock_validate_all.assert_called_once()

    @patch("cli.main.generate_metadata")
    def test_main_metadata(self, mock_generate_metadata):
        """Test main with metadata command."""
        mock_generate_metadata.return_value = 0
        with patch("sys.argv", ["porto", "metadata"]):
            result = main()
            assert result == 0
            mock_generate_metadata.assert_called_once()

    @patch("cli.main.create_parser")
    def test_main_no_command_shows_help(self, mock_create_parser):
        """Test main with no command shows help."""
        mock_parser = MagicMock()
        mock_parser.parse_args.return_value = MagicMock(command=None)
        mock_parser.print_help = MagicMock()
        mock_create_parser.return_value = mock_parser

        with patch("sys.argv", ["porto"]):
            result = main()
            assert result == 1
            mock_parser.print_help.assert_called_once()

    @patch("cli.main.create_parser")
    def test_main_invalid_validate_type(self, mock_create_parser):
        """Test main with invalid validate type."""
        mock_parser = MagicMock()
        mock_args = MagicMock()
        mock_args.command = "validate"
        mock_args.type = "invalid"
        mock_parser.parse_args.return_value = mock_args
        mock_parser.print_help = MagicMock()
        mock_create_parser.return_value = mock_parser

        with patch("sys.argv", ["porto", "validate", "--type", "invalid"]):
            result = main()
            assert result == 1
            mock_parser.print_help.assert_called_once()

    def test_main_entry_point_exits_with_code(self, project_root):
        """Test that running as __main__ (python -m cli.main) invokes main and exits."""
        env = {**os.environ, "PYTHONPATH": str(project_root)}
        result = subprocess.run(
            [sys.executable, "-m", "cli.main"],
            capture_output=True,
            text=True,
            cwd=str(project_root),
            env=env,
        )
        # No command or invalid: exit 1 and help on stderr/stdout
        assert result.returncode == 1
        assert "usage" in (result.stdout + result.stderr).lower() or "porto" in (
            result.stdout + result.stderr
        )

    def test_run_module_as_main_executes_guard(self, project_root, monkeypatch):
        """``python -m cli.main`` path: ``if __name__ == '__main__'`` calls ``sys.exit(main())``."""
        monkeypatch.chdir(project_root)
        monkeypatch.setenv("PYTHONPATH", str(project_root))
        # Only drop cli.main so other tests keep their cli.commands.* imports valid.
        sys.modules.pop("cli.main", None)
        with patch.object(sys, "argv", ["porto"]), patch.object(sys, "exit") as mock_exit:
            runpy.run_module("cli.main", run_name="__main__")
        mock_exit.assert_called_once_with(1)
