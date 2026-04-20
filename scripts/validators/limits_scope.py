"""Validate per-provider ``limits.json`` (not ``graph.json``).

For graph / ``graph.json`` consistency, use :mod:`scripts.validators.graph`.

Paths come from mappings.json via ``get_data_file_path("limits", provider_id)``.

Policy:
- limits[] = optional operator-specific rows that affect *letter* execution only.
- Sanctions / UN-EU style regimes live in policy/restrictions.json (not duplicated here).
- compliance_frameworks entries must align with the provider's operational timezone from
  policy/jurisdictions.json (jurisdictions[country].timezone for providers.json ``country``).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scripts.data_files import (
    PROVIDERS_REGISTRY_FILENAME,
    get_data_file_path,
    get_project_root,
)
from scripts.utils import load_json


def _registry_path(project_root: Path) -> Path:
    return project_root / PROVIDERS_REGISTRY_FILENAME


def _list_provider_ids(project_root: Path) -> list[str]:
    data = load_json(_registry_path(project_root))
    prov = data.get("providers") or {}
    if not isinstance(prov, dict):
        return []
    return sorted(prov.keys())


def _jurisdiction_country_timezones(project_root: Path) -> dict[str, str]:
    """Uppercase ISO alpha-2 → IANA from policy/jurisdictions.json."""
    candidates = [project_root / "policy" / "jurisdictions.json"]
    path: Path | None = next((p for p in candidates if p.is_file()), None)
    if path is None:
        try:
            path = get_data_file_path("jurisdictions", project_root=project_root)
        except FileNotFoundError:
            return {}
    if path is None or not path.is_file():
        return {}
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    j = doc.get("jurisdictions")
    if not isinstance(j, dict):
        return {}
    out: dict[str, str] = {}
    for key, bloc in j.items():
        if not isinstance(bloc, dict):
            continue
        if len(key) != 2 or not key.isalpha() or not key.isupper():
            continue
        tz = bloc.get("timezone")
        if isinstance(tz, str) and tz.strip():
            out[key] = tz.strip()
    return out


def _provider_timezones(project_root: Path) -> dict[str, str]:
    tz_map = _jurisdiction_country_timezones(project_root)
    data = load_json(_registry_path(project_root))
    providers = data.get("providers") or {}
    if not isinstance(providers, dict):
        return {}
    out: dict[str, str] = {}
    for pid, row in providers.items():
        if not isinstance(row, dict):
            continue
        cc = row.get("country")
        if not isinstance(cc, str) or len(cc.strip()) < 2:
            continue
        iso = cc.strip().upper()[:2]
        tz = tz_map.get(iso)
        if tz:
            out[pid] = tz
    return out


def validate_limits_scope(project_root: Path | None = None) -> int:
    """Run limits.json checks for every provider. Returns 0 if ok, 1 if errors."""
    root = project_root or get_project_root()
    errors: list[str] = []
    tz_by_provider = _provider_timezones(root)

    for provider_id in _list_provider_ids(root):
        try:
            path = get_data_file_path("limits", provider_id, project_root=root)
        except FileNotFoundError as e:
            errors.append(f"Cannot resolve limits file for provider '{provider_id}': {e}")
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

        expected_tz = tz_by_provider.get(provider_id)

        for fw_id, fw in frameworks.items():
            if not isinstance(fw, dict):
                errors.append(f"{path}: compliance_frameworks.{fw_id} must be an object")
                continue
            if expected_tz and fw.get("timezone") != expected_tz:
                errors.append(
                    f"{path}: framework {fw_id!r} timezone {fw.get('timezone')!r} "
                    f"!= policy/jurisdictions.json timezone {expected_tz!r} for {provider_id} "
                    f"(from providers.{provider_id}.country)"
                )

    if errors:
        for err in errors:
            print(f"❌ ERROR: {err}")
        print("\n🔧 FIX NEEDED: limits.json letter-scope validation failed.")
        return 1

    print("✅ limits.json checks passed for all providers (letter-send scope).")
    return 0
