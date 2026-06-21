"""Validate bundle layout: mappings.json (source of truth) vs disk, registry, metadata.

Checks:
  - ``mappings.providers`` keys match ``providers.json`` (bundle root) keys.
  - Each mapped data file under ``providers/<id>/`` exists.
  - Each mapped provider JSON has top-level ``provider`` equal to ``<id>`` (folder name).
  - No extra ``*.json`` files under ``providers/<id>/`` beyond what mappings list (letter bundle).
  - ``providers/<id>/`` exists for each registry id; no orphan provider folders.
  - If ``metadata.json`` exists: its ``providers`` keys match the registry.
"""

from __future__ import annotations

import json
from pathlib import Path

from scripts.data_files import (
    PROVIDERS_DIR,
    PROVIDERS_REGISTRY_FILENAME,
    _load_mappings_raw,
    get_project_root,
    load_providers_registry,
)
from scripts.validators.porto_ids import REQUIRED_PROVIDER_SCHEMAS


def validate_mappings_layout() -> int:
    """Run layout checks. Returns 0 if ok, 1 if errors."""
    root = get_project_root()
    print("Validating mappings (mappings.json ↔ providers ↔ metadata)...\n")

    errors: list[str] = []
    warnings: list[str] = []

    try:
        reg_doc = load_providers_registry()
    except FileNotFoundError as e:
        print(f"❌ ERROR: {e}")
        return 1
    except (json.JSONDecodeError, ValueError) as e:
        print(f"❌ ERROR: Invalid provider registry: {e}")
        return 1

    registry_ids = set(reg_doc["providers"])
    try:
        raw_mappings = _load_mappings_raw()
    except (FileNotFoundError, ValueError) as e:
        print(f"❌ ERROR: {e}")
        return 1

    providers_block_raw = raw_mappings.get(PROVIDERS_DIR)
    if not isinstance(providers_block_raw, dict):
        errors.append("mappings.json missing mappings.providers object")
        mapping_ids = set()
        providers_block: dict[str, object] = {}
    else:
        mapping_ids = set(providers_block_raw.keys())
        providers_block = providers_block_raw

    if registry_ids != mapping_ids:
        errors.append(
            f"mappings.json provider keys must match provider registry {PROVIDERS_REGISTRY_FILENAME}.\n"
            f"  registry only: {sorted(registry_ids - mapping_ids)}\n"
            f"  mappings only: {sorted(mapping_ids - registry_ids)}"
        )

    for pid in sorted(registry_ids):
        folder = root / PROVIDERS_DIR / pid
        if not folder.is_dir():
            errors.append(f"registry provider '{pid}' has no directory {folder}")

        pmap = providers_block.get(pid)
        if not isinstance(pmap, dict):
            if pid in registry_ids:
                errors.append(f"mappings.providers.{pid} must be an object")
            continue

        mapped_rel: set[str] = set()
        schema_keys = set(pmap.keys()) if isinstance(pmap, dict) else set()
        missing_schemas = sorted(set(REQUIRED_PROVIDER_SCHEMAS) - schema_keys)
        if missing_schemas:
            errors.append(
                f"mappings.providers.{pid} missing required schema mappings: {missing_schemas}"
            )

        for _schema, data_rel in pmap.items():
            if not isinstance(data_rel, str):
                errors.append(
                    f"mappings.providers.{pid}: data path must be string, got {type(data_rel)}"
                )
                continue
            mapped_rel.add(data_rel)
            data_path = root / data_rel
            if not data_path.is_file():
                errors.append(f"mapped file missing: {data_rel} (provider {pid})")
                continue
            if not data_rel.endswith(".json"):
                continue
            try:
                doc = json.loads(data_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                errors.append(f"{data_rel}: invalid JSON ({e})")
                continue
            if not isinstance(doc, dict):
                errors.append(f"{data_rel}: root must be a JSON object")
                continue
            doc_provider = doc.get("provider")
            if doc_provider is None:
                errors.append(
                    f"{data_rel}: missing top-level 'provider' field (must be '{pid}' per folder)"
                )
            elif doc_provider != pid:
                errors.append(
                    f"{data_rel}: top-level 'provider' is {doc_provider!r}, expected {pid!r} "
                    f"(must match providers/<id>/ folder)"
                )

        if folder.is_dir():
            json_on_disk = {p.name for p in folder.glob("*.json")}
            mapped_names = {Path(rel).name for rel in mapped_rel if rel.endswith(".json")}
            extra = sorted(json_on_disk - mapped_names)
            if extra:
                errors.append(
                    f"{PROVIDERS_DIR}/{pid}/: JSON file(s) not listed in mappings.json: {extra}. "
                    "Add them to mappings.providers or remove stray files."
                )

    providers_root = root / PROVIDERS_DIR
    if providers_root.is_dir():
        for entry in sorted(providers_root.iterdir()):
            if not entry.is_dir():
                continue
            if entry.name.startswith(".") or entry.name == "__pycache__":
                continue
            if entry.name not in registry_ids:
                errors.append(
                    f"folder {PROVIDERS_DIR}/{entry.name}/ is not listed in "
                    f"{PROVIDERS_REGISTRY_FILENAME}"
                )

    meta_path = root / "metadata.json"
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            errors.append(f"metadata.json is not valid JSON: {e}")
        else:
            meta_prov = meta.get("providers", {})
            if not isinstance(meta_prov, dict):
                errors.append("metadata.json 'providers' must be an object")
            else:
                meta_ids = set(meta_prov.keys())
                if meta_ids != registry_ids:
                    errors.append(
                        f"metadata.json provider keys must match {PROVIDERS_REGISTRY_FILENAME}.\n"
                        f"  registry only: {sorted(registry_ids - meta_ids)}\n"
                        f"  metadata only: {sorted(meta_ids - registry_ids)}\n"
                        "  Regenerate: python -m cli.main metadata"
                    )
    else:
        warnings.append(
            "metadata.json not found; skipped metadata provider-key check (run `porto metadata`)"
        )

    for w in warnings:
        print(f"⚠️  WARNING: {w}")
    if warnings:
        print()

    for err in errors:
        print(f"❌ ERROR: {err}")
    if errors:
        print()
        print("❌ Mappings validation failed.")
        return 1

    print(f"✅ Mappings OK ({len(registry_ids)} providers, files + provider field aligned).\n")
    return 0
