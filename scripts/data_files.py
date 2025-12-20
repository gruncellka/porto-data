"""Data files configuration and utilities.

This module provides:
- File name constants loaded from mappings.json
- Functions to work with data files and mappings
- Validation of required entities at import time

All data file information comes from mappings.json (single source of truth).
If mappings.json changes or is invalid, this module will fail at import time.
"""

import json
from pathlib import Path
from typing import Any, Dict


def _get_project_root() -> Path:
    """Determine project root by finding mappings.json relative to script location."""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    return project_root


def load_mappings(mappings_path: str | None = None) -> Dict[str, str]:
    """Load schema to data file mappings from mappings.json (source of truth).

    Args:
        mappings_path: Optional path to mappings.json. If None, automatically
            finds it in the project root (relative to script location).

    Returns:
        Dictionary mapping schema paths to data file paths.

    Raises:
        FileNotFoundError: If mappings.json doesn't exist
        ValueError: If mappings.json is invalid or empty
    """
    if mappings_path is None:
        project_root = _get_project_root()
        mappings_file = project_root / "mappings.json"
    else:
        mappings_file = Path(mappings_path)

    if not mappings_file.exists():
        raise FileNotFoundError(
            f"mappings.json not found at {mappings_file}. "
            "This file is the source of truth for schema-to-data file mappings. "
            f"Expected location: {_get_project_root() / 'mappings.json'}"
        )

    try:
        with open(mappings_file, encoding="utf-8") as f:
            mappings_data: Dict[str, Any] = json.load(f)
        mappings_raw = mappings_data.get("mappings", {})
        if not mappings_raw:
            raise ValueError(f"No mappings found in {mappings_file}")
        if not isinstance(mappings_raw, dict):
            raise ValueError(f"mappings must be a dictionary, got {type(mappings_raw)}")

        # Validate all values are strings
        mappings: Dict[str, str] = {}
        for key, value in mappings_raw.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValueError(
                    f"All mapping keys and values must be strings, got {type(key)} -> {type(value)}"
                )
            mappings[key] = value
        return mappings
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {mappings_file}: {e}") from e


def get_schema_data_mappings() -> Dict[str, str]:
    """Get the schema to data file mappings (alias for load_mappings)."""
    return load_mappings()


def get_all_data_file_names() -> dict[str, str]:
    """Get mapping of entity names to file names from mappings.json.

    Returns:
        Dictionary mapping entity names to file names
        (e.g., {"products": "products.json", "zones": "zones.json", ...})
    """
    mappings = load_mappings()
    entity_to_filename = {}

    for schema_path, data_path in mappings.items():
        # Extract entity name from schema path (e.g., "schemas/products.schema.json" -> "products")
        entity_name = Path(schema_path).stem.replace(".schema", "")
        # Extract filename from data path (e.g., "data/products.json" -> "products.json")
        filename = Path(data_path).name
        entity_to_filename[entity_name] = filename

    return entity_to_filename


def get_data_file_name(entity_name: str) -> str:
    """Get data file name from mappings.json by entity name.

    Args:
        entity_name: Entity name (e.g., 'products', 'zones', 'data_links', 'prices')

    Returns:
        Data file name (e.g., "products.json", "data_links.json")

    Raises:
        FileNotFoundError: If no mapping found for the entity name
    """
    mappings = load_mappings()
    schema_key = f"schemas/{entity_name}.schema.json"
    if schema_key in mappings:
        data_path = mappings[schema_key]
        return Path(data_path).name
    raise FileNotFoundError(
        f"No mapping found for '{entity_name}'. "
        f"Available entities: {[Path(k).stem.replace('.schema', '') for k in mappings]}"
    )


def get_data_file_path(entity_name: str) -> Path:
    """Get data file path from mappings by entity name.

    Args:
        entity_name: Entity name (e.g., 'products', 'zones', 'data_links')

    Returns:
        Path to the data file

    Raises:
        FileNotFoundError: If no mapping found for the entity name
    """
    mappings = get_schema_data_mappings()
    schema_key = f"schemas/{entity_name}.schema.json"
    if schema_key in mappings:
        project_root = _get_project_root()
        return project_root / mappings[schema_key]
    raise FileNotFoundError(
        f"No mapping found for '{entity_name}'. Available mappings: {list(mappings.keys())}"
    )


def get_data_files() -> set[str]:
    """Get set of data file names from mappings.json (for dependency validation).

    Used specifically for validating that files referenced in data_links.json
    dependencies are actual data files from mappings.json.

    Returns:
        Set of data file names (e.g., {"products.json", "services.json", ...}).
    """
    mappings = load_mappings()
    data_files = set()

    for data_path in mappings.values():
        filename = Path(data_path).name
        data_files.add(filename)

    return data_files


# ============================================================================
# File Name Constants - Loaded from mappings.json and validated at import
# ============================================================================

# Load file names from mappings.json (source of truth)
_FILE_NAMES = get_all_data_file_names()

# Required entities for data links validation
_REQUIRED_ENTITIES = [
    "data_links",
    "products",
    "zones",
    "weight_tiers",
    "services",
    "prices",
    "dimensions",
]

# Validate required entities exist - fail fast if mappings.json is incomplete
_missing = [e for e in _REQUIRED_ENTITIES if e not in _FILE_NAMES]
if _missing:
    raise ValueError(
        f"Missing required entities in mappings.json: {_missing}. "
        f"Available entities: {sorted(_FILE_NAMES.keys())}. "
        f"Please update mappings.json to include all required entities."
    )

# Export validated file name constants
# These are loaded from mappings.json and validated at import time
DATA_LINKS_FILE = _FILE_NAMES["data_links"]
PRODUCTS_FILE = _FILE_NAMES["products"]
ZONES_FILE = _FILE_NAMES["zones"]
WEIGHT_TIERS_FILE = _FILE_NAMES["weight_tiers"]
SERVICES_FILE = _FILE_NAMES["services"]
PRICES_FILE = _FILE_NAMES["prices"]
DIMENSIONS_FILE = _FILE_NAMES["dimensions"]

# Optional entities (with fallback)
FEATURES_FILE = _FILE_NAMES.get("features", "features.json")
RESTRICTIONS_FILE = _FILE_NAMES.get("restrictions", "restrictions.json")
