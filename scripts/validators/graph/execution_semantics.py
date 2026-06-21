"""Product ``mark_type`` / ``tracking_mode`` and optional tracking service linkage."""

from __future__ import annotations

from typing import Any

from scripts.data_files import GRAPH_FILE, PRODUCTS_FILE, SERVICES_FILE
from scripts.validators.base import ValidationResults

from .services import get_service_by_ref


def run_validate_execution_semantics(
    results: ValidationResults,
    *,
    graph: dict[str, Any] | None,
    products: dict[str, Any] | None,
    services: dict[str, Any] | None,
    services_by_id: dict[str, dict[str, Any]],
    product_dict: dict[str, dict[str, Any]],
) -> None:
    if products is None or services is None:
        return

    attached = (graph or {}).get("services") or []
    if not isinstance(attached, list):
        attached = []

    for product_id, product in product_dict.items():
        mark_type = product.get("mark_type")
        tracking_mode = product.get("tracking_mode")
        if mark_type is None or tracking_mode is None:
            results["errors"].append(
                f"Product '{product_id}' must define mark_type and tracking_mode ({PRODUCTS_FILE})"
            )
            continue

        if mark_type == "label" and tracking_mode == "none":
            results["errors"].append(
                f"Product '{product_id}': invalid combination label + tracking_mode none "
                f"(use optional or included)"
            )

        if tracking_mode != "optional":
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
            if not svc or not svc.get("enables_tracking"):
                continue
            if _service_covers_product(svc):
                ok = True
                break

        if not ok:
            for svc in services_by_id.values():
                if not svc.get("enables_tracking"):
                    continue
                if _service_covers_product(svc):
                    ok = True
                    break

        if not ok:
            results["errors"].append(
                f"Product '{product_id}' has tracking_mode optional but no service with "
                f"enables_tracking covers its zones in {SERVICES_FILE} / graph.services "
                f"({GRAPH_FILE})"
            )
