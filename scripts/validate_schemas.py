#!/usr/bin/env python3
"""Validate all JSON data files against their schemas."""

import json
import sys
from pathlib import Path

import tomllib
from jsonschema import Draft7Validator, ValidationError

from checksum_utils import get_schema_data_mappings, has_file_changes

# Get schema to data file mapping from shared module
VALIDATIONS = get_schema_data_mappings()


def load_project_metadata() -> dict:
    """Load basic metadata from pyproject.toml."""
    pyproject_path = Path("pyproject.toml")
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)
    project = data.get("project", {})
    return {
        "name": project.get("name", ""),
        "version": project.get("version", ""),
        "description": project.get("description", ""),
    }


# Metadata generation is handled by scripts/generate_metadata.py
# This ensures we have a single source of truth for metadata generation


def validate_file(schema_path: str, data_path: str) -> bool:
    """Validate a data file against its schema."""
    try:
        with open(schema_path) as f:
            schema = json.load(f)
        with open(data_path) as f:
            data = json.load(f)

        validator = Draft7Validator(schema)
        validator.validate(data)
        print(f"✓ {data_path}")
        return True

    except FileNotFoundError as e:
        print(f"✗ {data_path}: File not found - {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"✗ {data_path}: Invalid JSON - {e}")
        return False
    except ValidationError as e:
        print(f"✗ {data_path}: Validation failed")
        print(f"  Error: {e.message}")
        print(f"  Path: {'.'.join(str(p) for p in e.path)}")
        return False


def main():
    """Run all validations."""
    print("Validating JSON schemas...")
    print("=" * 60)

    failed = []
    for schema_path, data_path in VALIDATIONS.items():
        if not validate_file(schema_path, data_path):
            failed.append(data_path)

    print("=" * 60)
    if failed:
        print(f"✗ {len(failed)} file(s) failed validation:")
        for f in failed:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print(f"✓ All {len(VALIDATIONS)} files valid!")

        # Check if metadata needs updating
        if has_file_changes():
            print("")
            print("Changes detected, generating metadata.json...")
            try:
                # Use the centralized metadata generator
                import subprocess

                result = subprocess.run(
                    ["python3", "scripts/generate_metadata.py"],
                    capture_output=True,
                    text=True,
                    cwd=".",
                )
                if result.returncode == 0:
                    print("⚠️ metadata.json generated successfully!")
                else:
                    print(f"⚠ Warning: Could not generate metadata.json: {result.stderr}")
            except Exception as e:
                print(f"⚠ Warning: Could not generate metadata.json: {e}")
        else:
            print("")
            print("✓ No changes detected, skipping metadata generation")

        sys.exit(0)


if __name__ == "__main__":
    main()
