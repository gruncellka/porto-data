#!/usr/bin/env python3
"""Tests for CLI main module - comprehensive coverage."""

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
        args = parser.parse_args(["validate", "--type", "links", "--analyze"])
        assert args.analyze is True

    def test_create_parser_validate_default_type_is_none(self):
        """Test that validate with no --type has type None (run all)."""
        parser = create_parser()
        args = parser.parse_args(["validate"])
        assert args.type is None


class TestMainFunction:
    """Test main function with all code paths."""

    @patch("cli.main.validate_schema")
    def test_main_validate_schema(self, mock_validate_schema):
        """Test main with validate --type schema."""
        mock_validate_schema.return_value = 0
        with patch("sys.argv", ["porto", "validate", "--type", "schema"]):
            result = main()
            assert result == 0
            mock_validate_schema.assert_called_once()

    @patch("cli.main.validate_links")
    def test_main_validate_links(self, mock_validate_links):
        """Test main with validate --type links."""
        mock_validate_links.return_value = 0
        with patch("sys.argv", ["porto", "validate", "--type", "links"]):
            result = main()
            assert result == 0
            mock_validate_links.assert_called_once_with(analyze=False)

    @patch("cli.main.validate_links")
    def test_main_validate_links_with_analyze(self, mock_validate_links):
        """Test main with validate --type links --analyze."""
        mock_validate_links.return_value = 0
        with patch("sys.argv", ["porto", "validate", "--type", "links", "--analyze"]):
            result = main()
            assert result == 0
            mock_validate_links.assert_called_once_with(analyze=True)

    @patch("cli.main.validate_all")
    def test_main_validate_all(self, mock_validate_all):
        """Test main with validate and no --type runs all."""
        mock_validate_all.return_value = 0
        with patch("sys.argv", ["porto", "validate"]):
            result = main()
            assert result == 0
            mock_validate_all.assert_called_once()

    @patch("cli.main.validate_all")
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
