"""Pure helpers for envelope rectangles and layout/window views (no I/O)."""

from __future__ import annotations

from typing import Any

_RECT_KEYS = ("x", "y", "width", "height")


def envelope_rect_complete(r: Any) -> bool:
    """True if r is a dict with integer x, y, width, height."""
    if not isinstance(r, dict):
        return False
    return all(isinstance(r.get(k), int) for k in _RECT_KEYS)


def envelope_rect_equal(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return all(a.get(k) == b.get(k) for k in _RECT_KEYS)


def envelope_validation_views(env: dict[str, Any]) -> dict[str, Any]:
    """Nested layout.window or legacy top-level window flags."""
    rend = env.get("layout")
    if isinstance(rend, dict):
        win = rend.get("window") or {}
        sup = win.get("supported")
        wa = win.get("area") if sup is True else None
        return {
            "wa": wa,
            "has_w": envelope_rect_complete(wa),
            "no_window": sup is False,
            "force_window": sup is True,
        }
    wa_legacy = env.get("window_area")
    return {
        "wa": wa_legacy,
        "has_w": envelope_rect_complete(wa_legacy),
        "no_window": env.get("supports_window") is False,
        "force_window": env.get("window_supported") is True,
    }


def resolve_envelope_layout_row(
    jurisdictions: dict[str, Any],
    cc: str,
    eid: str,
) -> dict[str, Any] | None:
    """Return row with orientation+layout or None."""
    j = jurisdictions.get(cc)
    if not isinstance(j, dict):
        return None
    envs = j.get("envelopes")
    if not isinstance(envs, dict):
        return None
    row = envs.get(eid)
    if not isinstance(row, dict):
        return None
    if row.get("layout") is not None and row.get("orientation") is not None:
        return row
    return None
