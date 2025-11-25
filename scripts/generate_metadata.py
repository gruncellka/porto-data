#!/usr/bin/env python3
"""
Generate metadata.json with project info and file checksums.

Reads project metadata from pyproject.toml and generates checksums
for all schemas and data JSON files.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import tomllib

from utils import get_all_file_checksums, get_schema_data_mappings


def get_file_info(file_path: Path, base_path: Path, checksums: Dict[str, str]) -> Dict[str, Any]:
    """Get file metadata with checksum."""
    relative_path = file_path.relative_to(base_path)
    # Use as_posix() to normalize path separators to forward slashes
    # This matches the format in mappings.json and ensures cross-platform compatibility
    path_str = relative_path.as_posix()
    return {
        "path": path_str,
        "checksum": checksums.get(path_str, ""),
        "size": file_path.stat().st_size,
    }


def extract_entity_name(file_path: Path) -> str:
    """Extract entity name from filename (e.g., 'products' from 'products.json')."""
    name = file_path.stem
    # Remove .schema suffix if present
    if name.endswith(".schema"):
        name = name[:-7]
    return name


def get_schema_url(schema_path: Path) -> str:
    """Extract $id (canonical URL) from schema file."""
    try:
        with open(schema_path, encoding="utf-8") as f:
            schema: Dict[str, Any] = json.load(f)
        schema_id = schema.get("$id")
        if isinstance(schema_id, str):
            return schema_id
        return ""
    except (json.JSONDecodeError, FileNotFoundError, KeyError):
        return ""


def get_project_metadata(pyproject_path: Path) -> Dict[str, str]:
    """Extract project metadata from pyproject.toml."""
    with open(pyproject_path, "rb") as f:
        pyproject = tomllib.load(f)

    project = pyproject.get("project", {})
    return {
        "name": project.get("name", "unknown"),
        "version": project.get("version", "0.0.0"),
        "description": project.get("description", ""),
    }


def collect_files(
    directory: Path, pattern: str, base_path: Path, checksums: Dict[str, str]
) -> List[Dict[str, Any]]:
    """Collect all files matching pattern with their metadata."""
    files = []
    for file_path in sorted(directory.glob(pattern)):
        if file_path.is_file():
            files.append(get_file_info(file_path, base_path, checksums))
    return files


def generate_metadata() -> Dict[str, Any]:
    """Generate complete metadata dictionary."""
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    # Get project metadata
    pyproject_path = project_root / "pyproject.toml"
    project_meta = get_project_metadata(pyproject_path)

    # Get all file checksums
    checksums = get_all_file_checksums()

    # Get schema to data mappings
    mappings = get_schema_data_mappings()

    # Build entities structure grouped by entity name
    entities: Dict[str, Dict[str, Any]] = {}

    for schema_path_str, data_path_str in mappings.items():
        schema_path = project_root / schema_path_str
        data_path = project_root / data_path_str

        if not schema_path.exists() or not data_path.exists():
            continue

        # Extract entity name from data file
        entity_name = extract_entity_name(data_path)

        # Get schema URL from $id
        schema_url = get_schema_url(schema_path)

        # Build entity entry
        entities[entity_name] = {
            "data": get_file_info(data_path, project_root, checksums),
            "schema": {
                **get_file_info(schema_path, project_root, checksums),
                "url": schema_url,
            },
        }

    # Build metadata
    metadata = {
        "project": {
            "name": project_meta["name"],
            "version": project_meta["version"],
            "description": project_meta["description"],
        },
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "entities": entities,
        "checksums": {
            "algorithm": "SHA-256",
            "note": "Use checksums to verify data integrity and detect changes",
        },
    }

    return metadata


def main() -> None:
    """Main entry point."""
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    output_path = project_root / "metadata.json"

    print("Generating metadata...")
    print(f"Project root: {project_root}")

    # Check if metadata.json exists and if we need to regenerate
    has_changes = True  # Default to True for new files
    if output_path.exists():
        try:
            with open(output_path, encoding="utf-8") as f:
                existing_metadata = json.load(f)

            # Generate new metadata for comparison
            new_metadata = generate_metadata()

            # Compare the actual metadata content (excluding timestamp)
            existing_metadata_copy = existing_metadata.copy()
            new_metadata_copy = new_metadata.copy()

            # Remove timestamps for comparison
            existing_metadata_copy.pop("generated_at", None)
            new_metadata_copy.pop("generated_at", None)

            if existing_metadata_copy == new_metadata_copy:
                has_changes = False
            else:
                print("✓ Changes detected, updating metadata")
        except (json.JSONDecodeError, KeyError, FileNotFoundError):
            print("✓ No existing metadata found, generating new")
            new_metadata = generate_metadata()
            has_changes = True
    else:
        print("✓ No existing metadata found, generating new")
        new_metadata = generate_metadata()
        has_changes = True

    # Only write metadata.json if there are changes
    if has_changes:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(new_metadata, f, indent=4, ensure_ascii=False)
            f.write("\n")

        print(f"\n✓ Generated: {output_path}")
        print(
            f"  - Project: {new_metadata['project']['name']} v{new_metadata['project']['version']}"
        )
        print(f"  - Entities: {len(new_metadata['entities'])} entities")
        print(f"  - Generated at: {new_metadata['generated_at']}")
        print("  - Status: Updated (changes detected)")
    else:
        print("✓ No changes detected, keeping existing metadata")


if __name__ == "__main__":
    main()
