"""Product ``mark_type`` / ``tracking`` and optional tracking service linkage."""

from __future__ import annotations

from typing import Any

from scripts.data_files import GRAPH_FILE, PRODUCTS_FILE, SERVICES_FILE
from scripts.validators.base import ValidationResults

from .services import get_service_by_ref

TRACKING_KIND = "tracking"


def _features_by_id(features: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not features:
        return {}
    out: dict[str, dict[str, Any]] = {}
    for row in features.get("features") or []:
        if isinstance(row, dict) and row.get("id"):
            out[str(row["id"])] = row
    return out


def service_enables_tracking(
    svc: dict[str, Any],
    features_by_id: dict[str, dict[str, Any]],
) -> bool:
    """True iff ``features[]`` is a feature whose ``kind`` is tracking."""
    for ref in svc.get("features") or []:
        if not isinstance(ref, str):
            continue
        feat = features_by_id.get(ref)
        if isinstance(feat, dict) and feat.get("kind") == TRACKING_KIND:
            return True
    return False


def run_validate_execution_semantics(
    results: ValidationResults,
    *,
    graph: dict[str, Any] | None,
    products: dict[str, Any] | None,
    services: dict[str, Any] | None,
    services_by_id: dict[str, dict[str, Any]],
    product_dict: dict[str, dict[str, Any]],
    features: dict[str, Any] | None = None,
) -> None:
    if products is None or services is None:
        return

    attached = (graph or {}).get("services") or []
    if not isinstance(attached, list):
        attached = []

    features_by_id = _features_by_id(features)

    for product_id, product in product_dict.items():
        mark_type = product.get("mark_type")
        tracking = product.get("tracking")
        if mark_type is None or tracking is None:
            results["errors"].append(
                f"Product '{product_id}' must define mark_type and tracking ({PRODUCTS_FILE})"
            )
            continue

        if mark_type == "label" and tracking == "none":
            results["errors"].append(
                f"Product '{product_id}': invalid combination label + tracking none "
                f"(use optional or included)"
            )

        if tracking != "optional":
            continue

        p_zones = frozenset(product.get("zones") or [])

        def _service_covers_product(
            svc: dict[str, Any],
            *,
            product_zones: frozenset[str] = p_zones,
        ) -> bool:
            sz = svc.get("supported_zones")
            if not sz:
                return True
            return bool(set(product_zones) & set(sz))

        ok = False
        for sid in attached:
            svc = get_service_by_ref(services, str(sid))
            if not svc or not service_enables_tracking(svc, features_by_id):
                continue
            if _service_covers_product(svc):
                ok = True
                break

        if not ok:
            for svc in services_by_id.values():
                if not service_enables_tracking(svc, features_by_id):
                    continue
                if _service_covers_product(svc):
                    ok = True
                    break

        if not ok:
            results["errors"].append(
                f"Product '{product_id}' has tracking optional but no service with "
                f"feature kind {TRACKING_KIND!r} covers its zones in "
                f"{SERVICES_FILE} / graph.services ({GRAPH_FILE})"
            )
