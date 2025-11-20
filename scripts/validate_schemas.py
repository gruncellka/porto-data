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

        # Check if any data/schema files are staged
        import subprocess

        check_staged_data = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--", "data/", "schemas/"],
            capture_output=True,
            text=True,
            cwd=".",
        )
        data_files_staged = bool(check_staged_data.stdout.strip())

        # Check if metadata needs updating
        if has_file_changes():
            print("")
            print("Changes detected, generating metadata.json...")
            try:
                # Use the centralized metadata generator
                result = subprocess.run(
                    ["python3", "scripts/generate_metadata.py"],
                    capture_output=True,
                    text=True,
                    cwd=".",
                )
                if result.returncode == 0:
                    # Check if metadata.json was actually modified
                    check_modified = subprocess.run(
                        ["git", "diff", "--name-only", "metadata.json"],
                        capture_output=True,
                        text=True,
                        cwd=".",
                    )
                    metadata_modified = bool(check_modified.stdout.strip())

                    # Check if metadata.json is staged
                    check_staged_metadata = subprocess.run(
                        ["git", "diff", "--cached", "--name-only", "metadata.json"],
                        capture_output=True,
                        text=True,
                        cwd=".",
                    )
                    metadata_staged = bool(check_staged_metadata.stdout.strip())

                    # If data/schema files are staged and metadata needs updating but isn't staged, reject
                    if data_files_staged and metadata_modified and not metadata_staged:
                        print("")
                        print("❌ ERROR: metadata.json was generated but is not staged!")
                        print("")
                        print("data/schema files are staged, but metadata.json is not.")
                        print("Please stage metadata.json in the same commit:")
                        print("  git add metadata.json")
                        print("  git commit")
                        print("")
                        sys.exit(1)
                    elif metadata_modified and metadata_staged:
                        print("✓ metadata.json generated and staged")
                    elif metadata_modified:
                        print("✓ metadata.json generated (not needed for this commit)")
                    else:
                        print("✓ metadata.json up to date")
                else:
                    print(f"⚠ Warning: Could not generate metadata.json: {result.stderr}")
            except Exception as e:
                print(f"⚠ Warning: Could not generate metadata.json: {e}")
        else:
            # Even if no changes detected, check if metadata.json should be staged
            # (in case it was generated previously but not committed)
            if data_files_staged:
                check_modified = subprocess.run(
                    ["git", "diff", "--name-only", "metadata.json"],
                    capture_output=True,
                    text=True,
                    cwd=".",
                )
                metadata_modified = bool(check_modified.stdout.strip())

                check_staged_metadata = subprocess.run(
                    ["git", "diff", "--cached", "--name-only", "metadata.json"],
                    capture_output=True,
                    text=True,
                    cwd=".",
                )
                metadata_staged = bool(check_staged_metadata.stdout.strip())

                if metadata_modified and not metadata_staged:
                    print("")
                    print("❌ ERROR: metadata.json is modified but not staged!")
                    print("")
                    print(
                        "Data/schema files are staged, but metadata.json is modified and not staged."
                    )
                    print("Please stage metadata.json in the same commit:")
                    print("  git add metadata.json")
                    print("  git commit")
                    print("")
                    sys.exit(1)

            print("")
            print("✓ No changes detected, skipping metadata generation")

        sys.exit(0)


if __name__ == "__main__":
    main()
