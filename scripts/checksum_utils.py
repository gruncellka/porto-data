#!/usr/bin/env python3
"""
Shared utilities for checksum validation and change detection.

This module provides a centralized way to:
- Define schema and data file mappings
- Calculate file checksums
- Detect changes in files
- Validate metadata consistency
"""

import hashlib
import json
from pathlib import Path
from typing import Dict

# Centralized file mappings - single source of truth
SCHEMA_DATA_MAPPINGS = {
    "schemas/products.schema.json": "data/products.json",
    "schemas/services.schema.json": "data/services.json",
    "schemas/prices.schema.json": "data/prices.json",
    "schemas/zones.schema.json": "data/zones.json",
    "schemas/weight_tiers.schema.json": "data/weight_tiers.json",
    "schemas/dimensions.schema.json": "data/dimensions.json",
    "schemas/features.schema.json": "data/features.json",
    "schemas/restrictions.schema.json": "data/restrictions.json",
    "schemas/data_links.schema.json": "data/data_links.json",
}


def compute_checksum(file_path: str) -> str:
    """Compute SHA256 checksum for a given file."""
    with open(file_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def get_all_file_checksums() -> Dict[str, str]:
    """Get checksums for all schema and data files."""
    checksums = {}

    # Add schema files
    for schema_path in SCHEMA_DATA_MAPPINGS:
        if Path(schema_path).exists():
            checksums[schema_path] = compute_checksum(schema_path)

    # Add data files
    for data_path in SCHEMA_DATA_MAPPINGS.values():
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
    return SCHEMA_DATA_MAPPINGS.copy()
