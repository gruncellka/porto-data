"""SchemaValidator - validates JSON files against their schemas.

This module provides functions to validate JSON data files against their
corresponding JSON Schema definitions.
"""

import json
from pathlib import Path

from jsonschema import Draft7Validator, RefResolver, ValidationError

from scripts.data_files import get_all_schema_data_pairs, get_project_root

# Schema + data at bundle root (not listed in mappings.json to avoid self-reference).
BUNDLE_ROOT_SCHEMA_PAIRS: tuple[tuple[str, str], ...] = (
    ("schemas/mappings.schema.json", "mappings.json"),
    ("schemas/metadata.schema.json", "metadata.json"),
)

# ============================================================================
# Schema Validation Functions
# ============================================================================


def _schema_validator(schema_path: Path, schema: dict) -> Draft7Validator:
    """Build a Draft7Validator that resolves sibling schema $ref files."""
    schema_dir = schema_path.parent
    base_uri = schema_dir.as_uri() + "/"
    store: dict[str, dict] = {}
    for sibling in schema_dir.glob("*.schema.json"):
        with open(sibling, encoding="utf-8") as f:
            store[sibling.name] = json.load(f)
    resolver = RefResolver(base_uri=base_uri, referrer=schema, store=store)
    return Draft7Validator(schema, resolver=resolver)


def validate_file(schema_path: str, data_path: str) -> bool:
    """Validate a data file against its schema.

    Args:
        schema_path: Path to the schema file.
        data_path: Path to the data file.

    Returns:
        True if validation passes, False otherwise.
    """
    try:
        schema_file = Path(schema_path)
        with open(schema_file, encoding="utf-8") as f:
            schema = json.load(f)
        with open(data_path, encoding="utf-8") as f:
            data = json.load(f)

        validator = _schema_validator(schema_file, schema)
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
    pairs = get_all_schema_data_pairs()
    failed = []

    for schema_path, data_path in pairs:
        schema_full = root / schema_path
        data_full = root / data_path
        if not validate_file(str(schema_full), str(data_full)):
            failed.append(data_path)

    for schema_path, data_path in BUNDLE_ROOT_SCHEMA_PAIRS:
        schema_full = root / schema_path
        data_full = root / data_path
        if not validate_file(str(schema_full), str(data_full)):
            failed.append(data_path)

    print("=" * 60)
    total_ok = len(pairs) + len(BUNDLE_ROOT_SCHEMA_PAIRS)
    if failed:
        print(f"✗ {len(failed)} file(s) failed validation:")
        for f in failed:
            print(f"  - {f}")
        return 1
    else:
        print(f"✓ All {total_ok} files valid!")
        return 0
