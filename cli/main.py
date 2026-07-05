#!/usr/bin/env python3
"""Porto Data CLI - Single source of truth for all validation logic."""

import argparse
import sys

from cli.commands.metadata import generate_metadata


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
  porto validate --type mappings     mappings.json vs disk, providers.json registry, metadata alignment
  porto validate --type markets      policy/markets.json vs provider countries
  porto validate --type limits       Validate providers/*/limits.json (letter scope)
  porto validate --type porto_ids   Validate porto_id enums and native-id refs
  porto validate --type delivery         Zone delivery SLAs on products.json
  porto validate --type graph        Validate provider graph.json
  porto validate --type graph --analyze  Detailed graph analysis
  porto metadata                      Generate metadata.json
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands", metavar="COMMAND")

    # validate command
    validate_parser = subparsers.add_parser("validate", help="Validate data files")
    validate_parser.add_argument(
        "--type",
        choices=[
            "schema",
            "mappings",
            "markets",
            "limits",
            "porto_ids",
            "delivery",
            "graph",
        ],
        default=None,
        help="Type of validation to run (omit to run all)",
    )
    validate_parser.add_argument(
        "--analyze",
        action="store_true",
        help="Show detailed analysis (for graph validation only)",
    )

    # metadata command
    subparsers.add_parser("metadata", help="Generate metadata.json")

    return parser


def main() -> int:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if args.command == "validate":
        from cli.commands.validate import (
            validate_all,
            validate_delivery_cmd,
            validate_graph,
            validate_limits,
            validate_mappings,
            validate_markets_cmd,
            validate_porto_ids,
            validate_schema,
        )

        if args.type is not None and args.type not in (
            "schema",
            "mappings",
            "markets",
            "limits",
            "porto_ids",
            "delivery",
            "graph",
        ):
            parser.print_help()
            return 1
        if args.type == "schema":
            return validate_schema()
        if args.type == "mappings":
            return validate_mappings()
        if args.type == "markets":
            return validate_markets_cmd()
        if args.type == "limits":
            return validate_limits()
        if args.type == "porto_ids":
            return validate_porto_ids()
        if args.type == "delivery":
            return validate_delivery_cmd()
        if args.type == "graph":
            return validate_graph(analyze=args.analyze)
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
