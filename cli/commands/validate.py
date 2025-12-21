"""Validate command for porto CLI - thin wrapper around validators."""

import sys
from pathlib import Path

# Add scripts to path for imports
_scripts_dir = Path(__file__).parent.parent.parent / "scripts"
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

from validators.links import validate_data_links
from validators.schema import validate_all_schemas


def validate_schema() -> int:
    """Validate JSON schemas."""
    result: int = validate_all_schemas()
    return result


def validate_links(analyze: bool = False) -> int:
    """Validate data links."""
    result: int = validate_data_links(analyze=analyze)
    return result


def validate_all() -> int:
    """Validate everything (schemas and links)."""
    schema_result = validate_schema()
    if schema_result != 0:
        return schema_result
    return validate_links(analyze=False)
