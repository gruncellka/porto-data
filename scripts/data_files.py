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
    """Determine project root by finding mappings.json.

    Tries multiple locations:
    1. porto_data package (installed package; data is inside porto_data)
    2. Relative to script location (development: repo root or porto_data subdir)
    3. Current working directory

    Returns:
        Path to the directory containing mappings.json (and data/, schemas/)

    Raises:
        FileNotFoundError: If mappings.json cannot be found
    """
    # Try 1: porto_data package (installed wheel: data is inside the package)
    try:
        import porto_data

        root = Path(porto_data.__file__).parent
        if (root / "mappings.json").exists():
            return root
    except ImportError:
        pass

    # Try 2: Development mode — scripts' parent (repo root) or porto_data under it
    script_dir = Path(__file__).parent
    dev_root = script_dir.parent
    if (dev_root / "mappings.json").exists():
        return dev_root
    if (dev_root / "porto_data" / "mappings.json").exists():
        return dev_root / "porto_data"

    # Try 3: Current working directory (e.g. tests with tmp_path)
    cwd = Path.cwd()
    if (cwd / "mappings.json").exists():
        return cwd
    if (cwd / "porto_data" / "mappings.json").exists():
        return cwd / "porto_data"

    raise FileNotFoundError(
        "mappings.json not found. Tried:\n"
        "  1. porto_data package (installed)\n"
        f"  2. {dev_root} and {dev_root / 'porto_data'}\n"
        f"  3. {cwd} and {cwd / 'porto_data'}\n"
        "Run the CLI from the porto-data project root or install the package."
    )


def get_project_root() -> Path:
    """Return the project root (directory containing mappings.json and data/)."""
    return _get_project_root()


def load_mappings(mappings_path: str | None = None) -> Dict[str, str]:
    """Load schema to data file mappings from mappings.json (source of truth).

    Args:
        mappings_path: Optional path to mappings.json. If None, automatically
            finds it in the project root.

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
# NOTE: This is intentionally hardcoded (not derived from mappings.json) because:
# 1. It's a validation contract, not a source of truth
# 2. Ensures fail-fast if critical entities are missing
# 3. Separates business logic (requirements) from data structure (mappings.json)
# 4. Allows type-safe constant exports (DATA_LINKS_FILE, PRODUCTS_FILE, etc.)
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
