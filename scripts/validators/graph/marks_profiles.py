"""``marks.json`` profiles and product ``mark_profile`` references."""

from __future__ import annotations

from typing import Any

from scripts.data_files import MARKS_FILE
from scripts.validators.base import ValidationResults


def run_validate_marks_profiles(
    results: ValidationResults,
    *,
    graph: dict[str, Any] | None,
    products: dict[str, Any] | None,
    marks: dict[str, Any] | None,
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

    for product in products.get("products", []):
        if not isinstance(product, dict):
            continue
        product_id = product.get("id", "?")
        mp = product.get("mark_profile")
        chosen = str(mp) if isinstance(mp, str) and mp.strip() else default_id
        if not chosen:
            continue
        prof = by_id.get(chosen)
        if not prof:
            results["errors"].append(
                f"Product '{product_id}': mark_profile {chosen!r} not found in {MARKS_FILE}"
            )
            continue
        p_mark = product.get("mark_type")
        pr_mark = prof.get("mark_type")
        if p_mark != pr_mark:
            results["errors"].append(
                f"Product '{product_id}': mark_type {p_mark!r} does not match "
                f"marks profile {chosen!r} mark_type {pr_mark!r}"
            )
