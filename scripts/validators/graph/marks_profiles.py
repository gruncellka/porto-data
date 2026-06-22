"""``marks.json`` profiles and ``zones`` lane map."""

from __future__ import annotations

from typing import Any

from scripts.data_files import MARKS_FILE
from scripts.validators.base import ValidationResults


def _validate_profile_ref(
    results: ValidationResults,
    *,
    context: str,
    profile_id: str,
    by_id: dict[str, dict[str, Any]],
) -> None:
    if profile_id not in by_id:
        results["errors"].append(
            f"{context}: mark profile {profile_id!r} not found in {MARKS_FILE}"
        )


def run_validate_marks_profiles(
    results: ValidationResults,
    *,
    graph: dict[str, Any] | None,
    products: dict[str, Any] | None,
    marks: dict[str, Any] | None,
    zones: dict[str, Any] | None = None,
    services: dict[str, Any] | None = None,
) -> None:
    _ = products, services
    if not marks or not isinstance(marks, dict):
        results["errors"].append(f"Missing or invalid {MARKS_FILE} (expected file_type marks)")
        return
    if marks.get("file_type") != "marks":
        results["errors"].append(
            f"{MARKS_FILE}: file_type must be 'marks', got {marks.get('file_type')!r}"
        )
        return
    prov_graph = graph.get("provider") if graph else None
    prov_marks = marks.get("provider")
    if prov_graph and prov_marks and str(prov_graph) != str(prov_marks):
        results["errors"].append(
            f"{MARKS_FILE} provider '{prov_marks}' does not match graph provider '{prov_graph}'"
        )

    profiles_raw = marks.get("profiles")
    if not isinstance(profiles_raw, list) or not profiles_raw:
        results["errors"].append(f"{MARKS_FILE}: profiles must be a non-empty array")
        return

    by_id: dict[str, dict[str, Any]] = {}
    for row in profiles_raw:
        if not isinstance(row, dict) or not row.get("id"):
            results["errors"].append(f"{MARKS_FILE}: each profile must be an object with id")
            continue
        pid = str(row["id"])
        if pid in by_id:
            results["errors"].append(f"{MARKS_FILE}: duplicate profile id {pid!r}")
        by_id[pid] = row

    default_id = marks.get("default_profile")
    if not default_id or not isinstance(default_id, str):
        results["errors"].append(f"{MARKS_FILE}: default_profile must be a non-empty string")
    elif default_id not in by_id:
        results["errors"].append(
            f"{MARKS_FILE}: default_profile {default_id!r} not found in profiles"
        )

    zone_ids: set[str] = set()
    if zones and isinstance(zones, dict):
        zone_ids = {
            str(z["id"]) for z in zones.get("zones", []) if isinstance(z, dict) and z.get("id")
        }

    marks_zones = marks.get("zones")
    if not isinstance(marks_zones, dict) or not marks_zones:
        results["errors"].append(f"{MARKS_FILE}: zones must be a non-empty object")
        return

    for zone_id, profile_id in marks_zones.items():
        zone_s = str(zone_id)
        if zone_ids and zone_s not in zone_ids:
            results["errors"].append(f"{MARKS_FILE}: zones key {zone_s!r} not in zones.json")
        if not isinstance(profile_id, str) or not profile_id.strip():
            results["errors"].append(
                f"{MARKS_FILE}: zones[{zone_s!r}] must be a non-empty profile id string"
            )
            continue
        _validate_profile_ref(
            results,
            context=f"{MARKS_FILE} zones[{zone_s!r}]",
            profile_id=profile_id,
            by_id=by_id,
        )

    if zone_ids:
        missing = sorted(zone_ids - {str(k) for k in marks_zones})
        if missing:
            results["errors"].append(
                f"{MARKS_FILE}: zones missing entries for zones.json ids: {missing!r}"
            )
