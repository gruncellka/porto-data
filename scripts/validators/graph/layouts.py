"""Validation for global envelope layouts and product envelope id references."""

from __future__ import annotations

from typing import Any

from scripts.data_files import ENVELOPES_FILE, LAYOUTS_FILE
from scripts.validators.base import ValidationResults

from .envelope_geometry import (
    envelope_rect_complete,
    envelope_rect_equal,
    envelope_validation_views,
    resolve_envelope_layout_row,
)


def _envelope_format_ids(envelopes: dict[str, Any]) -> set[str]:
    return {f["id"] for f in envelopes.get("envelopes", []) if isinstance(f, dict) and f.get("id")}


def envelope_layout_geometry_errors(
    *,
    layout_fingerprint_id: str,
    path: str,
    env: dict[str, Any],
) -> list[str]:
    """Pure checks: address/print/window rectangles and consistency rules."""
    out: list[str] = []
    v = envelope_validation_views(env)
    addr = v["addr"]
    pa = v["pa"]
    wa = v["wa"]
    has_w = v["has_w"]
    no_window = v["no_window"]
    force_window = v["force_window"]
    prefix = f"Layout '{layout_fingerprint_id}' ({path})"

    if not envelope_rect_complete(addr):
        out.append(f"{prefix}: address_area must have integer x, y, width, height")
        return out
    if not envelope_rect_complete(pa):
        out.append(f"{prefix}: print_area must have integer x, y, width, height")
        return out
    if no_window and force_window:
        out.append(f"{prefix}: supports_window is false but window_supported is true")
        return out
    assert isinstance(addr, dict) and isinstance(pa, dict)
    if no_window:
        if has_w:
            out.append(f"{prefix}: supports_window is false; omit window_area")
        elif not envelope_rect_equal(addr, pa):
            out.append(f"{prefix}: without window, address_area must equal print_area")
    elif force_window:
        if not has_w:
            out.append(f"{prefix}: window_supported true requires window_area")
        elif not isinstance(wa, dict) or not envelope_rect_equal(addr, wa):
            out.append(
                f"{prefix}: address_area must equal window_area (identical x,y,width,height)"
            )
    elif has_w:
        assert isinstance(wa, dict)
        if not envelope_rect_equal(addr, wa):
            out.append(
                f"{prefix}: address_area must equal window_area (identical x,y,width,height)"
            )
    elif not envelope_rect_equal(addr, pa):
        out.append(f"{prefix}: no window_area; address_area must equal print_area")
    return out


def run_validate_layout_refs(
    results: ValidationResults,
    *,
    envelope_layouts: dict[str, Any] | None,
    envelopes: dict[str, Any] | None,
) -> None:
    if not envelope_layouts or not envelopes:
        return

    format_ids = _envelope_format_ids(envelopes)
    jurisdictions = envelope_layouts.get("jurisdictions")
    if not isinstance(jurisdictions, dict):
        return

    for cc, jblock in jurisdictions.items():
        if not isinstance(jblock, dict):
            continue
        envs = jblock.get("envelopes")
        if not isinstance(envs, dict):
            continue
        for eid, row in envs.items():
            if eid not in format_ids:
                results["errors"].append(
                    f"{LAYOUTS_FILE}: jurisdictions.{cc}.envelopes "
                    f"unknown envelope id {eid!r} (not in {ENVELOPES_FILE})"
                )
            if not isinstance(row, dict):
                continue
            resolved = resolve_envelope_layout_row(jurisdictions, str(cc), str(eid))
            if resolved is None:
                results["errors"].append(
                    f"{LAYOUTS_FILE}: jurisdictions.{cc}.envelopes.{eid} "
                    "must define orientation and layout"
                )


def run_validate_envelope_address_window(
    results: ValidationResults,
    *,
    envelope_layouts: dict[str, Any] | None,
) -> None:
    if not envelope_layouts:
        return
    jurisdictions = envelope_layouts.get("jurisdictions")
    if not isinstance(jurisdictions, dict):
        return

    for cc, jblock in jurisdictions.items():
        if not isinstance(jblock, dict):
            continue
        envs = jblock.get("envelopes")
        if not isinstance(envs, dict):
            continue
        for eid in envs:
            row = resolve_envelope_layout_row(jurisdictions, str(cc), str(eid))
            if not row or not isinstance(row, dict):
                continue
            fid = str(eid)
            env = {"layout": row.get("layout")}
            path = f"{LAYOUTS_FILE} ({cc}, {fid})"
            for msg in envelope_layout_geometry_errors(
                layout_fingerprint_id=fid, path=path, env=env
            ):
                results["errors"].append(msg)


def run_validate_envelope_ids(
    results: ValidationResults,
    *,
    envelopes: dict[str, Any] | None,
    products: dict[str, Any] | None,
) -> None:
    if not envelopes or not products:
        return

    format_ids = _envelope_format_ids(envelopes)
    for p in products.get("products", []):
        if not isinstance(p, dict):
            continue
        pid = p.get("id", "?")
        for eid in p.get("envelope_ids") or []:
            if eid not in format_ids:
                results["errors"].append(
                    f"Product '{pid}': envelope_id {eid!r} not found in {ENVELOPES_FILE}"
                )
