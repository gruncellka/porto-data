"""SchemaValidator - validates JSON files against their schemas.

This module provides functions to validate JSON data files against their
corresponding JSON Schema definitions.
"""

import json

from jsonschema import Draft7Validator, ValidationError

from scripts.data_files import get_project_root, get_schema_data_mappings

# ============================================================================
# Schema Validation Functions
# ============================================================================


def validate_file(schema_path: str, data_path: str) -> bool:
    """Validate a data file against its schema.

    Args:
        schema_path: Path to the schema file.
        data_path: Path to the data file.

    Returns:
        True if validation passes, False otherwise.
    """
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


def validate_all_schemas() -> int:
    """Validate all JSON files against their schemas.

    Returns:
        Exit code: 0 if all validations pass, 1 otherwise.
    """
    print("Validating JSON schemas...")
    print("=" * 60)

    root = get_project_root()
    validations = get_schema_data_mappings()
    failed = []

    for schema_path, data_path in validations.items():
        schema_full = root / schema_path
        data_full = root / data_path
        if not validate_file(str(schema_full), str(data_full)):
            failed.append(data_path)

    print("=" * 60)
    if failed:
        print(f"✗ {len(failed)} file(s) failed validation:")
        for f in failed:
            print(f"  - {f}")
        return 1
    else:
        print(f"✓ All {len(validations)} files valid!")
        return 0
