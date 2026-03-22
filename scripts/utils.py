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
from typing import Any

from scripts.data_files import get_all_schema_data_pairs, get_project_root


def compute_checksum(file_path: str) -> str:
    """Compute SHA256 checksum for a given file."""
    with open(file_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def get_all_file_checksums() -> dict[str, str]:
    """Get checksums for all schema and data files (for metadata generation).

    Uses get_all_schema_data_pairs to include all providers (deutschepost, swisspost, etc.).
    """
    root = get_project_root()
    checksums = {}
    pairs = get_all_schema_data_pairs()

    for schema_path, data_path in pairs:
        schema_full = root / schema_path
        if schema_full.exists():
            checksums[schema_path] = compute_checksum(str(schema_full))
        data_full = root / data_path
        if data_full.exists():
            checksums[data_path] = compute_checksum(str(data_full))

    return checksums


def _iter_metadata_entities(metadata: dict) -> list[dict]:
    """Yield entity dicts from metadata. Supports global+providers and legacy entities structure."""
    from scripts.data_files import GLOBAL_DIR, PROVIDERS_DIR

    entities = []
    if GLOBAL_DIR in metadata and PROVIDERS_DIR in metadata:
        for entity in metadata[GLOBAL_DIR].values():
            entities.append(entity)
        for provider_entities in metadata[PROVIDERS_DIR].values():
            for entity in provider_entities.values():
                entities.append(entity)
    elif "entities" in metadata:
        for entity in metadata["entities"].values():
            entities.append(entity)
    return entities


def get_existing_checksums_from_metadata(metadata_path: str = "metadata.json") -> dict[str, str]:
    """Extract existing checksums from metadata.json."""
    if not Path(metadata_path).exists():
        return {}

    try:
        with open(metadata_path) as f:
            metadata = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

    existing_checksums = {}
    for entity_data in _iter_metadata_entities(metadata):
        if "data" in entity_data and "path" in entity_data["data"]:
            existing_checksums[entity_data["data"]["path"]] = entity_data["data"].get(
                "checksum", ""
            )
        if "schema" in entity_data and "path" in entity_data["schema"]:
            existing_checksums[entity_data["schema"]["path"]] = entity_data["schema"].get(
                "checksum", ""
            )

    # Fallback to old structure for backward compatibility
    if "schemas" in metadata and "files" in metadata["schemas"]:
        for file_info in metadata["schemas"]["files"]:
            existing_checksums[file_info["path"]] = file_info["checksum"]
    if "data" in metadata and "files" in metadata["data"]:
        for file_info in metadata["data"]["files"]:
            existing_checksums[file_info["path"]] = file_info["checksum"]

    return existing_checksums


def has_file_changes() -> bool:
    """Check if any data or schema files have changed by comparing checksums.

    Checks both data/*.json and schemas/*.json files.
    Metadata is regenerated when any JSON file in mappings.json changes.
    """
    current_checksums = get_all_file_checksums()
    existing_checksums = get_existing_checksums_from_metadata()

    return current_checksums != existing_checksums


def load_json(filepath: Path | str) -> dict[str, Any]:
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
