#!/usr/bin/env python3
"""
Shared utilities for porto-data scripts.

This module provides:
- Calculate file checksums
- Detect changes in files
- Validate metadata consistency
- Load JSON files

Note: Data file mappings and related functions are in data_files.py
"""

import hashlib
import json
from pathlib import Path
from typing import Any, Dict

# Import from data_files for checksum functions
# Note: Both files are in scripts/ directory, so direct import works
from data_files import get_schema_data_mappings


def compute_checksum(file_path: str) -> str:
    """Compute SHA256 checksum for a given file."""
    with open(file_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def get_all_file_checksums() -> Dict[str, str]:
    """Get checksums for all schema and data files (for metadata generation)."""
    checksums = {}
    mappings = get_schema_data_mappings()

    # Add schema files
    for schema_path in mappings:
        if Path(schema_path).exists():
            checksums[schema_path] = compute_checksum(schema_path)

    # Add data files
    for data_path in mappings.values():
        if Path(data_path).exists():
            checksums[data_path] = compute_checksum(data_path)

    return checksums


def get_data_file_checksums() -> Dict[str, str]:
    """Get checksums for data files only (for change detection)."""
    checksums = {}
    mappings = get_schema_data_mappings()

    # Only data files - changes here trigger metadata regeneration
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
    """Check if any DATA files have changed by comparing checksums.

    Only checks data/*.json files, not schema files.
    This ensures metadata is only regenerated when data changes.
    """
    current_checksums = get_data_file_checksums()
    existing_checksums = get_existing_data_checksums_from_metadata()

    return current_checksums != existing_checksums


def get_existing_data_checksums_from_metadata(
    metadata_path: str = "metadata.json",
) -> Dict[str, str]:
    """Extract existing DATA file checksums from metadata.json."""
    if not Path(metadata_path).exists():
        return {}

    try:
        with open(metadata_path) as f:
            metadata = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

    existing_checksums = {}

    # Handle new structure with entities - only extract data checksums
    if "entities" in metadata:
        for _, entity_data in metadata["entities"].items():
            if "data" in entity_data and "path" in entity_data["data"]:
                existing_checksums[entity_data["data"]["path"]] = entity_data["data"].get(
                    "checksum", ""
                )

    return existing_checksums


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
