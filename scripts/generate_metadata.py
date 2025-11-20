#!/usr/bin/env python3
"""
Generate metadata.json with project info and file checksums.

Reads project metadata from pyproject.toml and generates checksums
for all schemas and data JSON files.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import tomllib

from checksum_utils import get_all_file_checksums


def get_file_info(file_path: Path, base_path: Path, checksums: Dict[str, str]) -> Dict[str, Any]:
    """Get file metadata with checksum."""
    relative_path = file_path.relative_to(base_path)
    return {
        "path": str(relative_path),
        "checksum": checksums.get(str(relative_path), ""),
        "size": file_path.stat().st_size,
    }


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

    # Collect schema files
    schema_dir = project_root / "schemas"
    schemas = collect_files(schema_dir, "*.json", project_root, checksums)

    # Collect data files
    data_dir = project_root / "data"
    data_files = collect_files(data_dir, "*.json", project_root, checksums)

    # Build metadata
    metadata = {
        "project": {
            "name": project_meta["name"],
            "version": project_meta["version"],
            "description": project_meta["description"],
        },
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "schemas": {
            "count": len(schemas),
            "files": schemas,
        },
        "data": {
            "count": len(data_files),
            "files": data_files,
        },
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
        print(f"  - Schemas: {new_metadata['schemas']['count']} files")
        print(f"  - Data: {new_metadata['data']['count']} files")
        print(f"  - Generated at: {new_metadata['generated_at']}")
        print("  - Status: Updated (changes detected)")
    else:
        print("✓ No changes detected, keeping existing metadata")


if __name__ == "__main__":
    main()
