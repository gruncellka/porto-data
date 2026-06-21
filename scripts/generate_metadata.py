#!/usr/bin/env python3
"""
Generate metadata.json with project info and file checksums.

Reads project metadata from pyproject.toml (or package metadata when installed),
builds checksums for all schema/data pairs from mappings.json, and adds a ``bundle``
section for ``mappings.json`` and ``providers.json`` (plus their schemas) so root
manifest files are explicit alongside the registry.
"""

import json
import tomllib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.data_files import (
    FORMATS_MAPPINGS_KEY,
    MAPPINGS_FILENAME,
    MAPPINGS_SCHEMA_RELPATH,
    POLICY_MAPPINGS_KEY,
    PROVIDERS_DIR,
    PROVIDERS_REGISTRY_FILENAME,
    PROVIDERS_SCHEMA_RELPATH,
    REGISTRY_MAPPINGS_KEY,
    get_all_schema_data_pairs,
    get_project_root,
)
from scripts.utils import get_all_file_checksums

# Package distribution name for fallback metadata (when not in repo)
DIST_NAME = "gruncellka-porto-data"

METADATA_SCHEMA_URI = (
    "https://raw.githubusercontent.com/gruncellka/porto-data/refs/heads/main/"
    "porto_data/schemas/metadata.schema.json"
)


def get_project_metadata(pyproject_path: Path) -> dict[str, str]:
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


def _project_meta_from_package() -> dict[str, str]:
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


def _get_project_meta(root: Path) -> dict[str, str]:
    """Project metadata from pyproject.toml (repo) or package (installed)."""
    pyproject = root.parent / "pyproject.toml"
    return get_project_metadata(pyproject) if pyproject.exists() else _project_meta_from_package()


def _file_info(path: Path, base: Path, checksums: dict[str, str]) -> dict[str, Any]:
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


def generate_metadata() -> dict[str, Any]:
    """Build full metadata dict (project, policy/formats/registry, providers, checksums, generated_at).

    Top-level keys ``policy``, ``formats``, ``registry`` mirror ``mappings.json`` blocks.
    """
    root = get_project_root()
    checksums = get_all_file_checksums()
    pairs = get_all_schema_data_pairs()
    project_meta = _get_project_meta(root)

    policy_entities: dict[str, dict[str, Any]] = {}
    formats_entities: dict[str, dict[str, Any]] = {}
    registry_entities: dict[str, dict[str, Any]] = {}
    providers_entities: dict[str, dict[str, Any]] = {}

    for schema_rel, data_rel in pairs:
        schema_path = root / schema_rel
        data_path = root / data_rel
        if not schema_path.exists() or not data_path.exists():
            continue
        name = _entity_name_from_path(data_path)
        schema_info = _file_info(schema_path, root, checksums)
        schema_info["url"] = _schema_url(schema_path)
        entity = {
            "data": _file_info(data_path, root, checksums),
            "schema": schema_info,
        }
        if data_rel.startswith("policy/"):
            policy_entities[name] = entity
        elif data_rel.startswith("formats/"):
            formats_entities[name] = entity
        elif data_rel == PROVIDERS_REGISTRY_FILENAME:
            registry_entities[name] = entity
        elif data_rel.startswith(f"{PROVIDERS_DIR}/"):
            provider = data_rel.split("/")[1]
            if provider not in providers_entities:
                providers_entities[provider] = {}
            providers_entities[provider][name] = entity

    bundle: dict[str, dict[str, Any]] = {}
    mappings_data = root / MAPPINGS_FILENAME
    mappings_schema = root / MAPPINGS_SCHEMA_RELPATH
    if mappings_data.exists() and mappings_schema.exists():
        ms = _file_info(mappings_schema, root, checksums)
        ms["url"] = _schema_url(mappings_schema)
        bundle["mappings"] = {
            "data": _file_info(mappings_data, root, checksums),
            "schema": ms,
        }
    registry_data = root / PROVIDERS_REGISTRY_FILENAME
    registry_schema = root / PROVIDERS_SCHEMA_RELPATH
    if registry_data.exists() and registry_schema.exists():
        rs = _file_info(registry_schema, root, checksums)
        rs["url"] = _schema_url(registry_schema)
        bundle["providers_registry"] = {
            "data": _file_info(registry_data, root, checksums),
            "schema": rs,
        }

    meta_out: dict[str, Any] = {
        "$schema": METADATA_SCHEMA_URI,
        "project": project_meta,
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        POLICY_MAPPINGS_KEY: policy_entities,
        FORMATS_MAPPINGS_KEY: formats_entities,
        REGISTRY_MAPPINGS_KEY: registry_entities,
        PROVIDERS_DIR: providers_entities,
        "checksums": {
            "algorithm": "SHA-256",
            "note": "Use checksums to verify data integrity and detect changes",
        },
    }
    if "mappings" in bundle and "providers_registry" in bundle:
        meta_out["bundle"] = bundle
    return meta_out


def _metadata_for_compare(meta: dict[str, Any]) -> dict[str, Any]:
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
        entity_count = (
            len(new_meta.get(POLICY_MAPPINGS_KEY, {}))
            + len(new_meta.get(FORMATS_MAPPINGS_KEY, {}))
            + len(new_meta.get(REGISTRY_MAPPINGS_KEY, {}))
            + sum(len(p) for p in new_meta.get(PROVIDERS_DIR, {}).values())
        )
        print(f"\n✓ Generated: {out_path}")
        print(f"  - Project: {new_meta['project']['name']} v{new_meta['project']['version']}")
        print(f"  - Entities: {entity_count} entities")
        print(f"  - Generated at: {new_meta['generated_at']}")
        print("  - Status: Updated (changes detected)")
    else:
        print("✓ No changes detected, keeping existing metadata")


if __name__ == "__main__":  # pragma: no cover
    main()
