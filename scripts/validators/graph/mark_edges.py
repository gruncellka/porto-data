"""``graph.json`` ``edges.marks``: zone (+ service) → mark profile resolution."""

from __future__ import annotations

from typing import Any

from scripts.data_files import GRAPH_FILE, MARKS_FILE
from scripts.validators.base import ValidationResults

from .edge_access import mark_edges, validate_edges_container


def _profile_ids(marks: dict[str, Any]) -> set[str]:
    profiles_raw = marks.get("profiles")
    if not isinstance(profiles_raw, list):
        return set()
    return {str(row["id"]) for row in profiles_raw if isinstance(row, dict) and row.get("id")}


def _validate_profile_ref(
    results: ValidationResults,
    *,
    context: str,
    profile_id: str,
    profile_ids: set[str],
) -> None:
    if profile_id not in profile_ids:
        results["errors"].append(
            f"{context}: mark profile {profile_id!r} not found in {MARKS_FILE}"
        )


def run_validate_mark_edges(
    results: ValidationResults,
    *,
    graph: dict[str, Any] | None,
    marks: dict[str, Any] | None,
    zones: dict[str, Any] | None = None,
) -> None:
    if not graph or not isinstance(graph, dict):
        return

    if not validate_edges_container(results, graph=graph):
        return

    marks_map = mark_edges(graph)

    if not marks or not isinstance(marks, dict):
        results["errors"].append(
            f"{GRAPH_FILE}: edges.marks requires {MARKS_FILE} (profiles catalog)"
        )
        return

    profile_ids = _profile_ids(marks)
    if not profile_ids:
        return

    zone_ids: set[str] = set()
    if zones and isinstance(zones, dict):
        zone_ids = {
            str(z["id"]) for z in zones.get("zones", []) if isinstance(z, dict) and z.get("id")
        }

    graph_services: set[str] = set()
    services_raw = graph.get("services")
    if isinstance(services_raw, list):
        graph_services = {str(s) for s in services_raw if isinstance(s, str)}

    if zone_ids and not marks_map:
        results["errors"].append(
            f"{GRAPH_FILE}: edges.marks must be non-empty when zones.json defines zones"
        )
        return

    for zone_id, edge in marks_map.items():
        zone_s = str(zone_id)
        if zone_ids and zone_s not in zone_ids:
            results["errors"].append(f"{GRAPH_FILE}: edges.marks key {zone_s!r} not in zones.json")
        if not isinstance(edge, dict):
            results["errors"].append(f"{GRAPH_FILE}: edges.marks[{zone_s!r}] must be an object")
            continue

        profile = edge.get("profile")
        if not isinstance(profile, str) or not profile.strip():
            results["errors"].append(
                f"{GRAPH_FILE}: edges.marks[{zone_s!r}].profile must be a non-empty string"
            )
        else:
            _validate_profile_ref(
                results,
                context=f"{GRAPH_FILE} edges.marks[{zone_s!r}].profile",
                profile_id=profile,
                profile_ids=profile_ids,
            )

        services_map = edge.get("services")
        if services_map is None:
            continue
        if not isinstance(services_map, dict):
            results["errors"].append(
                f"{GRAPH_FILE}: edges.marks[{zone_s!r}].services must be an object"
            )
            continue
        if not services_map:
            results["errors"].append(
                f"{GRAPH_FILE}: edges.marks[{zone_s!r}].services must be omitted or non-empty"
            )
            continue

        for service_id, profile_id in services_map.items():
            svc_s = str(service_id)
            if graph_services and svc_s not in graph_services:
                results["errors"].append(
                    f"{GRAPH_FILE}: edges.marks[{zone_s!r}].services key {svc_s!r} "
                    f"not in graph.services"
                )
            if not isinstance(profile_id, str) or not profile_id.strip():
                results["errors"].append(
                    f"{GRAPH_FILE}: edges.marks[{zone_s!r}].services[{svc_s!r}] "
                    "must be a non-empty profile id string"
                )
                continue
            _validate_profile_ref(
                results,
                context=f"{GRAPH_FILE} edges.marks[{zone_s!r}].services[{svc_s!r}]",
                profile_id=profile_id,
                profile_ids=profile_ids,
            )

    if zone_ids:
        missing = sorted(zone_ids - {str(k) for k in marks_map})
        if missing:
            results["errors"].append(
                f"{GRAPH_FILE}: edges.marks missing entries for zones.json ids: {missing!r}"
            )
        elif marks_map:
            results["correct"].append(
                f"{GRAPH_FILE}: edges.marks covers all {len(zone_ids)} zone(s)"
            )
