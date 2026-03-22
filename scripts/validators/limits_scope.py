"""Validate per-provider limits data for letter-send scope consistency.

Paths come from mappings.json via ``get_data_file_path("limits", provider_id)``.

Policy:
- limits[] = optional operator-specific rows that affect *letter* execution only.
- Sanctions / UN-EU style regimes live in global/restrictions.json (not duplicated here).
- compliance_frameworks entries must align with global/providers.json timezone for that provider.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts.data_files import (
    GLOBAL_DIR,
    PROVIDERS_REGISTRY_FILENAME,
    get_data_file_path,
    get_project_root,
)
from scripts.utils import load_json


def _registry_path(project_root: Path) -> Path:
    return project_root / GLOBAL_DIR / PROVIDERS_REGISTRY_FILENAME


def _list_provider_ids(project_root: Path) -> list[str]:
    data = load_json(_registry_path(project_root))
    prov = data.get("providers") or {}
    if not isinstance(prov, dict):
        return []
    return sorted(prov.keys())


def _provider_timezones(project_root: Path) -> dict[str, str]:
    data = load_json(_registry_path(project_root))
    providers = data.get("providers") or {}
    if not isinstance(providers, dict):
        return {}
    out: dict[str, str] = {}
    for pid, row in providers.items():
        if isinstance(row, dict) and row.get("timezone"):
            out[pid] = str(row["timezone"])
    return out


def validate_limits_scope(project_root: Path | None = None) -> int:
    """Run limits.json checks for every provider. Returns 0 if ok, 1 if errors."""
    root = project_root or get_project_root()
    errors: list[str] = []
    warnings: list[str] = []
    tz_by_provider = _provider_timezones(root)

    for provider_id in _list_provider_ids(root):
        try:
            path = get_data_file_path("limits", provider_id, project_root=root)
        except FileNotFoundError as e:
            errors.append(
                f"Cannot resolve limits file for provider '{provider_id}': {e}"
            )
            continue
        if not path.is_file():
            errors.append(f"Mapped limits file missing for '{provider_id}': {path}")
            continue
        try:
            data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            errors.append(f"{path}: invalid JSON ({e})")
            continue

        if data.get("file_type") != "limits":
            errors.append(f"{path}: file_type must be 'limits'")
        if data.get("provider") != provider_id:
            errors.append(
                f"{path}: provider field is {data.get('provider')!r}, "
                f"expected {provider_id!r} (must match folder name)"
            )

        limits = data.get("limits")
        if not isinstance(limits, list):
            errors.append(f"{path}: limits must be an array")
            continue

        frameworks = data.get("compliance_frameworks")
        if frameworks is None:
            errors.append(f"{path}: compliance_frameworks is required (use {{}} if empty)")
            continue
        if not isinstance(frameworks, dict):
            errors.append(f"{path}: compliance_frameworks must be an object")
            continue

        seen_ids: set[str] = set()
        for i, row in enumerate(limits):
            if not isinstance(row, dict):
                errors.append(f"{path}: limits[{i}] must be an object")
                continue
            rid = row.get("id")
            if not rid:
                errors.append(f"{path}: limits[{i}] missing id")
            elif rid in seen_ids:
                errors.append(f"{path}: duplicate limits id {rid!r}")
            else:
                seen_ids.add(str(rid))

            fw = row.get("framework_id")
            if fw is not None and fw not in frameworks:
                errors.append(
                    f"{path}: limits row {rid!r} references unknown framework_id {fw!r}"
                )

        expected_tz = tz_by_provider.get(provider_id)
        referenced_fw: set[str] = set()
        for row in limits:
            if isinstance(row, dict) and row.get("framework_id"):
                referenced_fw.add(str(row["framework_id"]))

        for fw_id, fw in frameworks.items():
            if not isinstance(fw, dict):
                errors.append(f"{path}: compliance_frameworks.{fw_id} must be an object")
                continue
            if expected_tz and fw.get("timezone") != expected_tz:
                errors.append(
                    f"{path}: framework {fw_id!r} timezone {fw.get('timezone')!r} "
                    f"!= global/providers.json timezone {expected_tz!r} for {provider_id}"
                )

        for fw_id in frameworks:
            if fw_id not in referenced_fw:
                warnings.append(
                    f"{path}: compliance_frameworks.{fw_id} is not referenced by any limits row"
                )

    for w in warnings:
        print(f"⚠️  WARNING: {w}")
    if errors:
        for e in errors:
            print(f"❌ ERROR: {e}")
        print("\n🔧 FIX NEEDED: limits.json letter-scope validation failed.")
        return 1

    print("✅ limits.json checks passed for all providers (letter-send scope).")
    return 0
