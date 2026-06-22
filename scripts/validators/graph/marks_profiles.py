"""``marks.json`` profiles and mark profile references on products, graph edges, and services."""

from __future__ import annotations

from typing import Any

from scripts.data_files import MARKS_FILE
from scripts.validators.base import ValidationResults


def _profile_mark_type_mismatch(
    results: ValidationResults,
    *,
    context: str,
    profile_id: str,
    expected_mark_type: Any,
    prof: dict[str, Any],
) -> None:
    pr_mark = prof.get("mark_type")
    if expected_mark_type != pr_mark:
        results["errors"].append(
            f"{context}: mark_type {expected_mark_type!r} does not match "
            f"marks profile {profile_id!r} mark_type {pr_mark!r}"
        )


def _validate_profile_ref(
    results: ValidationResults,
    *,
    context: str,
    profile_id: str,
    by_id: dict[str, dict[str, Any]],
    expected_mark_type: Any | None = None,
) -> dict[str, Any] | None:
    prof = by_id.get(profile_id)
    if not prof:
        results["errors"].append(
            f"{context}: mark profile {profile_id!r} not found in {MARKS_FILE}"
        )
        return None
    if expected_mark_type is not None:
        _profile_mark_type_mismatch(
            results,
            context=context,
            profile_id=profile_id,
            expected_mark_type=expected_mark_type,
            prof=prof,
        )
    return prof


def _validate_mark_profile_by_zone(
    results: ValidationResults,
    *,
    context: str,
    zone_map: Any,
    allowed_zones: set[str],
    by_id: dict[str, dict[str, Any]],
    expected_mark_type: Any | None = None,
) -> None:
    if zone_map is None:
        return
    if not isinstance(zone_map, dict) or not zone_map:
        results["errors"].append(f"{context}: mark_profile_by_zone must be a non-empty object")
        return
    for zone, profile_id in zone_map.items():
        zone_s = str(zone)
        if zone_s not in allowed_zones:
            results["errors"].append(
                f"{context}: mark_profile_by_zone key {zone_s!r} not in allowed zones {sorted(allowed_zones)!r}"
            )
        if not isinstance(profile_id, str) or not profile_id.strip():
            results["errors"].append(
                f"{context}: mark_profile_by_zone[{zone_s!r}] must be a non-empty profile id string"
            )
            continue
        _validate_profile_ref(
            results,
            context=f"{context} mark_profile_by_zone[{zone_s!r}]",
            profile_id=profile_id,
            by_id=by_id,
            expected_mark_type=expected_mark_type,
        )


def run_validate_marks_profiles(
    results: ValidationResults,
    *,
    graph: dict[str, Any] | None,
    products: dict[str, Any] | None,
    marks: dict[str, Any] | None,
    services: dict[str, Any] | None = None,
) -> None:
    if products is None:
        return
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

    product_dict: dict[str, dict[str, Any]] = {}
    for product in products.get("products", []):
        if not isinstance(product, dict):
            continue
        product_key = product.get("id")
        if isinstance(product_key, str) and product_key:
            product_dict[product_key] = product

    edges = graph.get("edges", {}) if graph else {}
    if isinstance(edges, dict):
        for product_id, edge in edges.items():
            if not isinstance(edge, dict):
                continue
            zones_raw = edge.get("zones", [])
            allowed_zones = {str(z) for z in zones_raw if isinstance(z, str)}
            product = product_dict.get(str(product_id))
            expected_mark_type = product.get("mark_type") if product else None
            _validate_mark_profile_by_zone(
                results,
                context=f"graph.edges[{product_id!r}]",
                zone_map=edge.get("mark_profile_by_zone"),
                allowed_zones=allowed_zones,
                by_id=by_id,
                expected_mark_type=expected_mark_type,
            )

    for service in (services or {}).get("services", []):
        if not isinstance(service, dict):
            continue
        service_id = service.get("id", "?")
        supported = service.get("supported_zones")
        allowed_zones = (
            {str(z) for z in supported if isinstance(z, str)}
            if isinstance(supported, list) and supported
            else set()
        )
        mp = service.get("mark_profile")
        if isinstance(mp, str) and mp.strip():
            _validate_profile_ref(
                results,
                context=f"services[{service_id!r}].mark_profile",
                profile_id=mp,
                by_id=by_id,
            )
        zone_map = service.get("mark_profile_by_zone")
        if zone_map is not None and not allowed_zones:
            results["warnings"].append(
                f"services[{service_id!r}]: mark_profile_by_zone set but supported_zones "
                "omitted — zone keys not validated against service scope"
            )
        _validate_mark_profile_by_zone(
            results,
            context=f"services[{service_id!r}]",
            zone_map=zone_map,
            allowed_zones=allowed_zones if allowed_zones else {str(k) for k in zone_map or {}},
            by_id=by_id,
        )

    for product in products.get("products", []):
        if not isinstance(product, dict):
            continue
        product_id = product.get("id", "?")
        mp = product.get("mark_profile")
        chosen = str(mp) if isinstance(mp, str) and mp.strip() else default_id
        if not chosen:
            continue
        prof = _validate_profile_ref(
            results,
            context=f"Product '{product_id}'",
            profile_id=chosen,
            by_id=by_id,
            expected_mark_type=product.get("mark_type"),
        )
        if prof is None:
            continue
