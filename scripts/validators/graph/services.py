"""``graph.services``, service price rows, and service reference helpers."""

from __future__ import annotations

from typing import Any

from scripts.data_files import GRAPH_FILE, SERVICE_PRICES_FILE, SERVICES_FILE
from scripts.validators.base import ValidationResults


def service_ids_set(services: dict[str, Any] | None) -> set[str]:
    """Native ``services[].id`` strings valid in graph/prices/rules."""
    if not services:
        return set()
    return {
        str(s["id"]) for s in services.get("services", []) if isinstance(s, dict) and s.get("id")
    }


def get_service_by_id(services: dict[str, Any] | None, service_id: str) -> dict[str, Any] | None:
    """Resolve a service row by native ``id``."""
    if not services or not service_id:
        return None
    for s in services.get("services", []):
        if isinstance(s, dict) and s.get("id") == service_id:
            return s
    return None


# Backward-compatible aliases for graph package internals
service_refs_set = service_ids_set
get_service_by_ref = get_service_by_id


def run_validate_service_prices(
    results: ValidationResults,
    *,
    services: dict[str, Any] | None,
    service_prices: list[dict[str, Any]],
) -> None:
    """Validate that service and price ``effective_to`` dates match."""
    for price_entry in service_prices:
        service_id = price_entry.get("service_id")
        if not service_id:
            continue

        price_entries = price_entry.get("price", [])
        price_effective_to = None
        for price_item in price_entries:
            effective_to = price_item.get("effective_to")
            if effective_to is not None:
                price_effective_to = effective_to
                break

        if price_effective_to is not None:
            service = get_service_by_id(services, str(service_id))
            if not service:
                results["errors"].append(
                    f"Service '{service_id}' has prices but service not found in services.json"
                )
                continue

            service_effective_to = service.get("effective_to")

            if service_effective_to is None:
                results["errors"].append(
                    f"Service '{service_id}' has prices with effective_to='{price_effective_to}' "
                    f"but service does not have effective_to set. Service must be marked as discontinued "
                    f"when prices are discontinued. "
                    f"Price found in: {SERVICE_PRICES_FILE} -> service_prices. "
                    f"Service found in: {SERVICES_FILE} -> services"
                )
            elif service_effective_to != price_effective_to:
                results["errors"].append(
                    f"Service '{service_id}' has price effective_to='{price_effective_to}' "
                    f"but service effective_to='{service_effective_to}'. Dates must match. "
                    f"Price found in: {SERVICE_PRICES_FILE} -> service_prices. "
                    f"Service found in: {SERVICES_FILE} -> services"
                )


def run_validate_graph_services(
    results: ValidationResults,
    *,
    graph: dict[str, Any],
    services: dict[str, Any] | None,
    service_prices: list[dict[str, Any]],
) -> None:
    """Validate ``graph.services`` native ids and service-price consistency."""
    attached = graph.get("services", [])

    valid_ids = service_ids_set(services)
    for sp in service_prices:
        sid = sp.get("service_id")
        if not sid:
            continue
        if str(sid) not in valid_ids:
            results["errors"].append(
                f"Service '{sid}' in service_prices does not exist in {SERVICES_FILE} "
                f"(native id required). Found in: {SERVICE_PRICES_FILE} -> service_prices"
            )

    for service_id in attached:
        if service_id not in valid_ids:
            results["errors"].append(
                f"Service '{service_id}' in graph.services does not exist in {SERVICES_FILE}. "
                f"Found in: {GRAPH_FILE} -> services"
            )

    service_price_ids = {sp.get("service_id") for sp in service_prices}
    for service_id in attached:
        if service_id not in service_price_ids:
            results["warnings"].append(
                f"Service '{service_id}' is listed as available but has no row in {SERVICE_PRICES_FILE}"
            )

    run_validate_service_prices(results, services=services, service_prices=service_prices)
