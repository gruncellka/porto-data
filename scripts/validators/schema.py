"""SchemaValidator - validates JSON files against their schemas.

This module provides functions to validate JSON data files against their
corresponding JSON Schema definitions.
"""

import json
from pathlib import Path
from typing import Any, Dict, cast

from jsonschema import Draft7Validator, RefResolver, ValidationError
from referencing.exceptions import Unresolvable

from scripts.data_files import get_schema_data_mappings

# ============================================================================
# Schema Validation Functions
# ============================================================================


def _build_store(schema_path: Path) -> Dict[str, dict]:
    """Provide local copies for known canonical definitions to avoid remote fetches."""
    store: Dict[str, dict] = {}
    project_root = schema_path.parent.parent  # .../schemas -> project root
    definitions_dir = project_root / "definitions"

    for path in definitions_dir.rglob("*.schema.json"):
        with open(path) as f:
            content = json.load(f)
        content = dict(content)
        canonical_id = content.pop("$id", None)  # strip to avoid scope changes
        file_uri = path.resolve().as_uri()

        store[file_uri] = content
        if canonical_id:
            store[canonical_id] = content

    return store


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

        # Resolve $ref relative to the schema file location to avoid remote fetches
        schema_file = Path(schema_path).resolve()
        base_uri = schema_file.as_uri()
        # Override resolution scope locally to avoid remote fetches while keeping on-disk $id canonical.
        schema = dict(schema)
        schema.pop("$id", None)  # avoid remote scope; use local base_uri
        store = _build_store(schema_file)
        resolver = RefResolver(
            base_uri=base_uri,
            referrer=schema,
            store=cast(Any, store),  # mypy: store accepts arbitrary schema objects
        )
        validator = Draft7Validator(schema, resolver=resolver)
        validator.validate(data)
        print(f"✓ {data_path}")
        return True

    except FileNotFoundError as e:
        print(f"✗ {data_path}: File not found - {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"✗ {data_path}: Invalid JSON - {e}")
        return False
    except Unresolvable as e:
        print(f"✗ {data_path}: Schema $ref could not be resolved - {e}")
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

    validations = get_schema_data_mappings()
    failed = []

    for schema_path, data_path in validations.items():
        if not validate_file(schema_path, data_path):
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
