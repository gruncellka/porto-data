"""``marks.json`` profile catalog. Resolution lives in ``graph.edges.marks``."""

from __future__ import annotations

from typing import Any

from scripts.data_files import ENVELOPES_FILE, GRAPH_FILE, LAYOUTS_FILE, MARKS_FILE
from scripts.validators.base import ValidationResults

from .edge_access import wire_ids
from .envelope_geometry import envelope_rect_complete, envelope_rect_on_face

_DIM_KEYS = ("width_px", "height_px", "width_mm", "height_mm")


def run_validate_marks_profiles(
    results: ValidationResults,
    *,
    graph: dict[str, Any] | None,
    marks: dict[str, Any] | None,
    envelopes: dict[str, Any] | None = None,
    envelope_layouts: dict[str, Any] | None = None,
    provider_id: str | None = None,
) -> None:
    if not marks or not isinstance(marks, dict):
        results["errors"].append(f"Missing or invalid {MARKS_FILE} (expected file_type marks)")
        return
    if marks.get("file_type") != "marks":
        results["errors"].append(
            f"{MARKS_FILE}: file_type must be 'marks', got {marks.get('file_type')!r}"
        )
        return

    if marks.get("provider") is not None:
        results["errors"].append(
            f"{MARKS_FILE}: top-level 'provider' is path-implied — remove redundant field"
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
        wire_ids=wire_ids(graph),
    )
    _validate_placement(
        results,
        marks=marks,
        profiles=by_id,
        envelopes=envelopes,
        provider_id=provider_id,
    )
    _validate_address_zone_vs_window(
        results,
        marks=marks,
        envelope_layouts=envelope_layouts,
        provider_id=provider_id,
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

        wire = row.get("wire")
        if not isinstance(wire, str) or not wire.strip():
            results["errors"].append(f"{prefix}: wire must be a non-empty string")
        elif wire_ids and wire.strip().lower() not in wire_ids:
            results["errors"].append(
                f"{prefix}: wire {wire.strip().lower()!r} must match a key in "
                f"{GRAPH_FILE} edges.wire (have {sorted(wire_ids)})"
            )

        layout = row.get("mark_profile")
        if not isinstance(layout, str) or not layout.strip():
            results["errors"].append(f"{prefix}: mark_profile must be a non-empty string")

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


def _envelope_faces(envelopes: dict[str, Any] | None) -> dict[str, tuple[int, int]]:
    out: dict[str, tuple[int, int]] = {}
    if not envelopes:
        return out
    for row in envelopes.get("envelopes") or []:
        if not isinstance(row, dict) or not row.get("id"):
            continue
        try:
            out[str(row["id"])] = (int(row["width"]), int(row["height"]))
        except (TypeError, ValueError, KeyError):
            continue
    return out


def _validate_placement(
    results: ValidationResults,
    *,
    marks: dict[str, Any],
    profiles: dict[str, dict[str, Any]],
    envelopes: dict[str, Any] | None,
    provider_id: str | None,
) -> None:
    placement = marks.get("placement")
    if placement is None:
        return
    prefix = f"{MARKS_FILE}: placement"
    if not isinstance(placement, dict):
        results["errors"].append(f"{prefix} must be an object")
        return
    envelopes_map = placement.get("envelopes")
    if not isinstance(envelopes_map, dict) or not envelopes_map:
        results["errors"].append(f"{prefix}.envelopes must be a non-empty object")
        return

    faces = _envelope_faces(envelopes)
    skip_size_fit = provider_id == "swisspost"

    for envelope_id, rect in envelopes_map.items():
        loc = f"{prefix}.envelopes.{envelope_id}"
        if envelope_id not in faces:
            results["errors"].append(
                f"{loc}: unknown envelope id {envelope_id!r} (not in {ENVELOPES_FILE})"
            )
            continue
        if not envelope_rect_complete(rect):
            results["errors"].append(f"{loc}: must have integer x, y, width, height")
            continue
        face_w, face_h = faces[envelope_id]
        if not envelope_rect_on_face(rect, width=face_w, height=face_h):
            results["errors"].append(
                f"{loc}: rectangle is not on the envelope face ({face_w}×{face_h})"
            )
            continue
        if skip_size_fit:
            continue
        for profile_id, profile in profiles.items():
            size = profile.get("size")
            if not isinstance(size, dict):
                continue
            width = size.get("width")
            height = size.get("height")
            if not isinstance(width, int) or not isinstance(height, int):
                continue
            extra = 0.0
            clearance = profile.get("clearance")
            if clearance is not None:
                try:
                    extra = 2.0 * float(clearance)
                except (TypeError, ValueError):
                    results["errors"].append(
                        f"{MARKS_FILE}: profiles[{profile_id!r}].clearance must be a number"
                    )
                    continue
            if width + extra > rect["width"] or height + extra > rect["height"]:
                results["errors"].append(
                    f"{MARKS_FILE}: profile {profile_id!r} size "
                    f"{width}×{height} (+clearance) does not fit {loc} "
                    f"{rect['width']}×{rect['height']}"
                )


def _validate_address_zone_vs_window(
    results: ValidationResults,
    *,
    marks: dict[str, Any],
    envelope_layouts: dict[str, Any] | None,
    provider_id: str | None,
) -> None:
    """ADDRESS_ZONE canvas vs DE window size — catalog consistency of two facts."""
    if provider_id != "deutschepost" or not envelope_layouts:
        return
    canvas = None
    for row in marks.get("calibrations") or []:
        if isinstance(row, dict) and row.get("mark_profile") == "ADDRESS_ZONE":
            canvas = row.get("label_canvas")
            break
    if not isinstance(canvas, dict):
        return
    canvas_w = canvas.get("width_mm")
    canvas_h = canvas.get("height_mm")
    if not isinstance(canvas_w, (int, float)) or not isinstance(canvas_h, (int, float)):
        return

    de = (envelope_layouts.get("jurisdictions") or {}).get("DE")
    if not isinstance(de, dict):
        return
    envelopes = de.get("envelopes")
    if not isinstance(envelopes, dict):
        return
    for envelope_id, row in envelopes.items():
        if not isinstance(row, dict):
            continue
        window = (row.get("layout") or {}).get("window") or {}
        if window.get("supported") is not True:
            continue
        area = window.get("area") or {}
        width = area.get("width")
        height = area.get("height")
        if not isinstance(width, int) or not isinstance(height, int):
            continue
        if canvas_w > width or canvas_h > height:
            results["errors"].append(
                f"{MARKS_FILE}: ADDRESS_ZONE label_canvas {canvas_w}×{canvas_h} "
                f"does not fit {LAYOUTS_FILE} DE {envelope_id} window {width}×{height}"
            )
