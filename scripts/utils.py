#!/usr/bin/env python3
"""
Shared utilities for porto-data scripts.

This module provides a centralized way to:
- Define schema and data file mappings
- Calculate file checksums
- Detect changes in files
- Validate metadata consistency
- Load JSON files
- Get data file lists
- Get data file paths by entity name
"""

import hashlib
import json
from pathlib import Path
from typing import Any, Dict


def _get_project_root() -> Path:
    """Determine project root by finding mappings.json relative to script location."""
    # Get the directory where this script is located (scripts/)
    script_dir = Path(__file__).parent
    # Project root is one level up from scripts/
    project_root = script_dir.parent
    return project_root


def load_mappings(mappings_path: str | None = None) -> Dict[str, str]:
    """Load schema to data file mappings from mappings.json (source of truth).

    Args:
        mappings_path: Optional path to mappings.json. If None, automatically
            finds it in the project root (relative to script location).

    Returns:
        Dictionary mapping schema paths to data file paths.
    """
    if mappings_path is None:
        # Automatically determine project root and find mappings.json
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
        # Type check and convert to Dict[str, str]
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


def compute_checksum(file_path: str) -> str:
    """Compute SHA256 checksum for a given file."""
    with open(file_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def get_all_file_checksums() -> Dict[str, str]:
    """Get checksums for all schema and data files."""
    checksums = {}
    mappings = load_mappings()

    # Add schema files
    for schema_path in mappings:
        if Path(schema_path).exists():
            checksums[schema_path] = compute_checksum(schema_path)

    # Add data files
    for data_path in mappings.values():
        if Path(data_path).exists():
            checksums[data_path] = compute_checksum(data_path)

    return checksums


def get_existing_checksums_from_metadata(metadata_path: str = "metadata.json") -> Dict[str, str]:
    """Extract existing checksums from metadata.json."""
    if not Path(metadata_path).exists():
        return {}

    try:
        with open(metadata_path) as f:
            metadata = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

    existing_checksums = {}

    # Handle new structure with entities
    if "entities" in metadata:
        for _, entity_data in metadata["entities"].items():
            # Extract data file checksum
            if "data" in entity_data and "path" in entity_data["data"]:
                existing_checksums[entity_data["data"]["path"]] = entity_data["data"].get(
                    "checksum", ""
                )
            # Extract schema file checksum
            if "schema" in entity_data and "path" in entity_data["schema"]:
                existing_checksums[entity_data["schema"]["path"]] = entity_data["schema"].get(
                    "checksum", ""
                )
    # Fallback to old structure for backward compatibility
    else:
        # Extract schema checksums
        if "schemas" in metadata and "files" in metadata["schemas"]:
            for file_info in metadata["schemas"]["files"]:
                existing_checksums[file_info["path"]] = file_info["checksum"]

        # Extract data checksums
        if "data" in metadata and "files" in metadata["data"]:
            for file_info in metadata["data"]["files"]:
                existing_checksums[file_info["path"]] = file_info["checksum"]

    return existing_checksums


def has_file_changes() -> bool:
    """Check if any files have changed by comparing checksums."""
    current_checksums = get_all_file_checksums()
    existing_checksums = get_existing_checksums_from_metadata()

    return current_checksums != existing_checksums


def get_schema_data_mappings() -> Dict[str, str]:
    """Get the schema to data file mappings."""
    return load_mappings()


def load_json(filepath: Path | str) -> Dict[str, Any]:
    """Load and parse JSON file.

    Args:
        filepath: Path to JSON file (Path object or string).

    Returns:
        Parsed JSON data as dictionary.

    Raises:
        FileNotFoundError: If file doesn't exist.
        json.JSONDecodeError: If file contains invalid JSON.
    """
    path = Path(filepath) if isinstance(filepath, str) else filepath
    with open(path, encoding="utf-8") as f:
        return json.load(f)  # type: ignore[no-any-return]


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
    # Find schema file that matches entity name
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
        # Extract filename from path (e.g., "data/products.json" -> "products.json")
        filename = Path(data_path).name
        data_files.add(filename)

    return data_files
