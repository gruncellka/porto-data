"""``marks.json`` profile catalog. Resolution lives in ``graph.edges.marks``."""

from __future__ import annotations

from typing import Any

from scripts.data_files import GRAPH_FILE, MARKS_FILE
from scripts.validators.base import ValidationResults

from .edge_access import wire_integration_ids

_DIM_KEYS = ("width_px", "height_px", "width_mm", "height_mm")


def run_validate_marks_profiles(
    results: ValidationResults,
    *,
    graph: dict[str, Any] | None,
    marks: dict[str, Any] | None,
) -> None:
    if not marks or not isinstance(marks, dict):
        results["errors"].append(f"Missing or invalid {MARKS_FILE} (expected file_type marks)")
        return
    if marks.get("file_type") != "marks":
        results["errors"].append(
            f"{MARKS_FILE}: file_type must be 'marks', got {marks.get('file_type')!r}"
        )
        return

    provider_id = graph.get("provider") if isinstance(graph, dict) else None
    if provider_id and marks.get("provider") and str(provider_id) != str(marks.get("provider")):
        results["errors"].append(
            f"{MARKS_FILE} provider {marks.get('provider')!r} does not match "
            f"{GRAPH_FILE} provider {provider_id!r}"
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

    if marks.get("zones") is not None:
        results["errors"].append(
            f"{MARKS_FILE}: zones is removed; use {GRAPH_FILE} edges.marks for resolution"
        )

    _validate_calibrations(
        results,
        marks=marks,
        profile_ids=set(by_id.keys()),
        wire_ids=wire_integration_ids(graph),
    )


def _validate_dimension_box(
    results: ValidationResults,
    *,
    prefix: str,
    box: Any,
    label: str,
) -> bool:
    if not isinstance(box, dict):
        results["errors"].append(f"{prefix}: {label} must be an object")
        return False
    ok = True
    for key in _DIM_KEYS:
        if key not in box:
            results["errors"].append(f"{prefix}: {label} missing {key!r}")
            ok = False
    return ok


def _validate_calibrations(
    results: ValidationResults,
    *,
    marks: dict[str, Any],
    profile_ids: set[str],
    wire_ids: frozenset[str],
) -> None:
    calibrations = marks.get("calibrations")
    if calibrations is None:
        return
    if not isinstance(calibrations, list):
        results["errors"].append(f"{MARKS_FILE}: calibrations must be an array when present")
        return

    for index, row in enumerate(calibrations):
        if not isinstance(row, dict):
            results["errors"].append(f"{MARKS_FILE}: calibrations[{index}] must be an object")
            continue
        prefix = f"{MARKS_FILE}: calibrations[{index}]"

        integration = row.get("integration")
        if not isinstance(integration, str) or not integration.strip():
            results["errors"].append(f"{prefix}: integration must be a non-empty string")
        elif wire_ids and integration.strip().lower() not in wire_ids:
            results["errors"].append(
                f"{prefix}: integration {integration.strip().lower()!r} must match a key in "
                f"{GRAPH_FILE} edges.wire (have {sorted(wire_ids)})"
            )

        layout = row.get("voucher_layout")
        if not isinstance(layout, str) or not layout.strip():
            results["errors"].append(f"{prefix}: voucher_layout must be a non-empty string")

        by_profile = row.get("by_mark_profile")
        canvas = row.get("label_canvas")
        has_profile_map = isinstance(by_profile, dict) and bool(by_profile)
        has_canvas = canvas is not None

        if not has_profile_map and not has_canvas:
            results["errors"].append(
                f"{prefix}: requires by_mark_profile or label_canvas dimension data"
            )
            continue

        if has_profile_map and isinstance(by_profile, dict):
            for profile_id, dims in by_profile.items():
                if profile_id not in profile_ids:
                    results["errors"].append(
                        f"{prefix}: by_mark_profile key {profile_id!r} not in profiles"
                    )
                _validate_dimension_box(
                    results,
                    prefix=prefix,
                    box=dims,
                    label=f"by_mark_profile[{profile_id!r}]",
                )

        if has_canvas:
            _validate_dimension_box(results, prefix=prefix, box=canvas, label="label_canvas")

        if row.get("source_run") is not None:
            results["errors"].append(f"{prefix}: source_run must not be set in porto-data")
