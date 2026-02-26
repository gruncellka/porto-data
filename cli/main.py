#!/usr/bin/env python3
"""Porto Data CLI - Single source of truth for all validation logic."""

import argparse
import sys

# Import commands
from cli.commands.metadata import generate_metadata
from cli.commands.validate import validate_all, validate_links, validate_schema


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="porto",
        description="Porto Data validation and management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  porto validate                      Validate everything (default)
  porto validate --type schema        Validate JSON schemas
  porto validate --type links         Validate data links
  porto validate --type links --analyze  Detailed links analysis
  porto metadata                      Generate metadata.json
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands", metavar="COMMAND")

    # validate command
    validate_parser = subparsers.add_parser("validate", help="Validate data files")
    validate_parser.add_argument(
        "--type",
        choices=["schema", "links"],
        default=None,
        help="Type of validation to run (omit to run all)",
    )
    validate_parser.add_argument(
        "--analyze",
        action="store_true",
        help="Show detailed analysis (for links validation only)",
    )

    # metadata command
    subparsers.add_parser("metadata", help="Generate metadata.json")

    return parser


def main() -> int:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if args.command == "validate":
        if args.type is not None and args.type not in ("schema", "links"):
            parser.print_help()
            return 1
        if args.type == "schema":
            return validate_schema()
        elif args.type == "links":
            return validate_links(analyze=args.analyze)
        else:
            # no --type: validate everything
            return validate_all()
    elif args.command == "metadata":
        return generate_metadata()
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
