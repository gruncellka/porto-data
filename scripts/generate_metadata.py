#!/usr/bin/env python3
"""
Generate metadata.json with project info and file checksums.

Reads project metadata from pyproject.toml (or package metadata when installed)
and builds checksums for all schema/data files from mappings.json.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import tomllib

from scripts.data_files import get_project_root, get_schema_data_mappings
from scripts.utils import get_all_file_checksums

# Package distribution name for fallback metadata (when not in repo)
DIST_NAME = "gruncellka-porto-data"


def get_project_metadata(pyproject_path: Path) -> Dict[str, str]:
    """Extract project name/version/description from pyproject.toml. Public for tests."""
    if not pyproject_path.exists():
        return _project_meta_from_package()
    with open(pyproject_path, "rb") as f:
        project = tomllib.load(f).get("project", {})
    return {
        "name": project.get("name", DIST_NAME),
        "version": project.get("version", "0.0.0"),
        "description": project.get("description", ""),
    }


def _project_meta_from_package() -> Dict[str, str]:
    """Read name/version/description from installed package metadata."""
    from importlib.metadata import metadata as pkg_meta

    pkg = pkg_meta(DIST_NAME)

    def _pkg(key: str, default: str) -> str:
        try:
            return pkg[key]
        except KeyError:
            return default

    return {
        "name": _pkg("Name", DIST_NAME),
        "version": _pkg("Version", "0.0.0"),
        "description": _pkg("Summary", ""),
    }


def _get_project_meta(root: Path) -> Dict[str, str]:
    """Project metadata from pyproject.toml (repo) or package (installed)."""
    pyproject = root.parent / "pyproject.toml"
    return get_project_metadata(pyproject) if pyproject.exists() else _project_meta_from_package()


def _file_info(path: Path, base: Path, checksums: Dict[str, str]) -> Dict[str, Any]:
    """Single file entry: path (relative), checksum, size."""
    rel = path.relative_to(base).as_posix()
    return {
        "path": rel,
        "checksum": checksums.get(rel, ""),
        "size": path.stat().st_size,
    }


def _schema_url(schema_path: Path) -> str:
    """$id from schema JSON, or empty."""
    try:
        with open(schema_path, encoding="utf-8") as f:
            url = json.load(f).get("$id")
        return url if isinstance(url, str) else ""
    except (json.JSONDecodeError, FileNotFoundError, KeyError):
        return ""


def _entity_name_from_path(path: Path) -> str:
    """e.g. products.json -> products; products.schema.json -> products."""
    name = path.stem
    return name[:-7] if name.endswith(".schema") else name


# Public aliases for tests
extract_entity_name = _entity_name_from_path
get_file_info = _file_info
get_schema_url = _schema_url


def generate_metadata() -> Dict[str, Any]:
    """Build full metadata dict (project, entities, checksums, generated_at)."""
    root = get_project_root()
    checksums = get_all_file_checksums()
    mappings = get_schema_data_mappings()
    project_meta = _get_project_meta(root)

    entities: Dict[str, Dict[str, Any]] = {}
    for schema_rel, data_rel in mappings.items():
        schema_path = root / schema_rel
        data_path = root / data_rel
        if not schema_path.exists() or not data_path.exists():
            continue
        name = _entity_name_from_path(data_path)
        schema_info = _file_info(schema_path, root, checksums)
        schema_info["url"] = _schema_url(schema_path)
        entities[name] = {
            "data": _file_info(data_path, root, checksums),
            "schema": schema_info,
        }

    return {
        "project": project_meta,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "entities": entities,
        "checksums": {
            "algorithm": "SHA-256",
            "note": "Use checksums to verify data integrity and detect changes",
        },
    }


def _metadata_for_compare(meta: Dict[str, Any]) -> Dict[str, Any]:
    """Copy without generated_at for equality check."""
    out = meta.copy()
    out.pop("generated_at", None)
    return out


def main() -> None:
    """Generate metadata.json under project root; only write if content changed."""
    root = get_project_root()
    out_path = root / "metadata.json"

    print("Generating metadata...")
    print(f"Project root: {root}")

    new_meta = generate_metadata()
    write = True
    if out_path.exists():
        try:
            with open(out_path, encoding="utf-8") as f:
                existing = json.load(f)
            if _metadata_for_compare(existing) == _metadata_for_compare(new_meta):
                write = False
            else:
                print("✓ Changes detected, updating metadata")
        except (json.JSONDecodeError, KeyError, FileNotFoundError):
            print("✓ No existing metadata found, generating new")
    else:
        print("✓ No existing metadata found, generating new")

    if write:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(new_meta, f, indent=4, ensure_ascii=False)
            f.write("\n")
        print(f"\n✓ Generated: {out_path}")
        print(f"  - Project: {new_meta['project']['name']} v{new_meta['project']['version']}")
        print(f"  - Entities: {len(new_meta['entities'])} entities")
        print(f"  - Generated at: {new_meta['generated_at']}")
        print("  - Status: Updated (changes detected)")
    else:
        print("✓ No changes detected, keeping existing metadata")


if __name__ == "__main__":
    main()
