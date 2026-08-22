"""Validate formats/addresses.json jurisdiction keys and layout standard parity."""

from __future__ import annotations

import json
import re
from typing import Any

from scripts.data_files import _get_project_root

_ADDRESSES_REL = "formats/addresses.json"
_LAYOUTS_REL = "formats/layouts.json"
_FORM_KINDS = frozenset({"street", "post_box"})


def _load_json(relative: str) -> dict[str, Any]:
    path = _get_project_root() / relative
    with open(path, encoding="utf-8") as f:
        data: Any = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{relative}: expected object root")
    return data


def _known_alpha2_codes(jurisdictions_doc: dict[str, Any]) -> set[str]:
    """Collect ISO 3166-1 alpha-2 codes from policy/jurisdictions.json."""
    known: set[str] = set()
    root = jurisdictions_doc.get("jurisdictions")
    if not isinstance(root, dict):
        return known
    alpha2 = re.compile(r"^[A-Z]{2}$")
    for key, row in root.items():
        code = str(key).upper()
        if alpha2.match(code):
            known.add(code)
        if isinstance(row, dict):
            members = row.get("members")
            if isinstance(members, list):
                for member in members:
                    if isinstance(member, str) and alpha2.match(member.upper()):
                        known.add(member.upper())
    return known


def _layout_standard_for_jurisdiction(layouts_doc: dict[str, Any], code: str) -> str | None:
    """Return the unique layout standard token for a jurisdiction, or None if absent."""
    jurisdictions = layouts_doc.get("jurisdictions")
    if not isinstance(jurisdictions, dict):
        return None
    row = jurisdictions.get(code)
    if not isinstance(row, dict):
        return None
    envelopes = row.get("envelopes")
    if not isinstance(envelopes, dict) or not envelopes:
        return None
    standards: set[str] = set()
    for env_row in envelopes.values():
        if isinstance(env_row, dict) and isinstance(env_row.get("standard"), str):
            standards.add(env_row["standard"])
    if len(standards) == 1:
        return next(iter(standards))
    if len(standards) > 1:
        return f"__ambiguous__:{','.join(sorted(standards))}"
    return None


def _validate_forms(key: str, form: dict[str, Any], errors: list[str]) -> None:
    forms = form.get("forms")
    if not isinstance(forms, list) or not forms:
        errors.append(f"addresses.jurisdictions.{key}: forms must be a non-empty array")
        return
    seen: set[str] = set()
    for index, row in enumerate(forms):
        prefix = f"addresses.jurisdictions.{key}.forms[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{prefix}: must be an object")
            continue
        kind = row.get("kind")
        if kind not in _FORM_KINDS:
            errors.append(f"{prefix}: kind must be one of {sorted(_FORM_KINDS)}")
            continue
        if kind in seen:
            errors.append(f"addresses.jurisdictions.{key}: duplicate form kind {kind!r}")
        seen.add(str(kind))
        required = row.get("required")
        if not isinstance(required, list) or not required:
            errors.append(f"{prefix}: required must be a non-empty array")


def validate_addresses() -> int:
    """Validate address forms vs jurisdictions policy and layouts standards."""
    errors: list[str] = []
    try:
        addresses_doc = _load_json(_ADDRESSES_REL)
        layouts_doc = _load_json(_LAYOUTS_REL)
        jurisdictions_doc = _load_json("policy/jurisdictions.json")
    except (OSError, ValueError, json.JSONDecodeError) as e:
        print(f"addresses: failed to load inputs: {e}")
        return 1

    forms = addresses_doc.get("jurisdictions")
    if not isinstance(forms, dict) or not forms:
        print("addresses: jurisdictions must be a non-empty object")
        return 1

    known = _known_alpha2_codes(jurisdictions_doc)
    alpha2 = re.compile(r"^[A-Z]{2}$")
    for code, form in forms.items():
        key = str(code).upper()
        if not alpha2.match(key):
            errors.append(
                f"addresses.jurisdictions.{code}: key must be ISO 3166-1 alpha-2 uppercase"
            )
            continue
        if known and key not in known:
            errors.append(
                f"addresses.jurisdictions.{key}: unknown jurisdiction "
                "(not in policy/jurisdictions.json)"
            )
        if not isinstance(form, dict):
            errors.append(f"addresses.jurisdictions.{key}: form must be an object")
            continue
        addr_standard = form.get("standard")
        if not isinstance(addr_standard, str) or not addr_standard:
            errors.append(f"addresses.jurisdictions.{key}: standard is required")
            continue
        _validate_forms(key, form, errors)
        layout_standard = _layout_standard_for_jurisdiction(layouts_doc, key)
        # Layout match only when a layout jurisdiction exists (UA may be address-only).
        if layout_standard is None:
            continue
        if layout_standard.startswith("__ambiguous__:"):
            errors.append(
                f"addresses.jurisdictions.{key}: layouts have conflicting standards "
                f"({layout_standard.split(':', 1)[1]})"
            )
        elif addr_standard != layout_standard:
            errors.append(
                f"addresses.jurisdictions.{key}: standard {addr_standard!r} must match "
                f"layouts standard {layout_standard!r}"
            )

    if errors:
        for err in errors:
            print(err)
        print(f"addresses: {len(errors)} error(s)")
        return 1
    print("addresses: OK")
    return 0
