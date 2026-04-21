"""``available_services``, service price rows, and service reference helpers."""

from __future__ import annotations

from typing import Any

from scripts.data_files import GRAPH_FILE, SERVICE_PRICES_FILE, SERVICES_FILE
from scripts.validators.base import ValidationResults


def service_refs_set(services: dict[str, Any] | None) -> set[str]:
    """Provider ``id`` and unified ``porto_id`` strings that may appear in graph/prices."""
    if not services:
        return set()
    out: set[str] = set()
    for s in services.get("services", []):
        if s.get("id"):
            out.add(str(s["id"]))
        if s.get("porto_id"):
            out.add(str(s["porto_id"]))
    return out


def get_service_by_ref(services: dict[str, Any] | None, ref: str) -> dict[str, Any] | None:
    """Resolve a service row by provider ``id`` or ``porto_id``."""
    if not services or not ref:
        return None
    for s in services.get("services", []):
        if isinstance(s, dict) and (s.get("id") == ref or s.get("porto_id") == ref):
            return s
    return None


def run_validate_service_price_consistency(
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
            service = get_service_by_ref(services, str(service_id))
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


def run_validate_available_services(
    results: ValidationResults,
    *,
    graph: dict[str, Any],
    services: dict[str, Any] | None,
    service_prices: list[dict[str, Any]],
) -> None:
    """Validate ``available_services`` and service-price consistency."""
    available_services = graph.get("global_settings", {}).get("available_services", [])

    valid_refs = service_refs_set(services)
    for sp in service_prices:
        sid = sp.get("service_id")
        if not sid:
            continue
        if str(sid) not in valid_refs:
            results["errors"].append(
                f"Service '{sid}' in service_prices does not exist in {SERVICES_FILE} "
                f"(by id or porto_id). Found in: {SERVICE_PRICES_FILE} -> service_prices"
            )

    for service_id in available_services:
        if service_id not in valid_refs:
            results["errors"].append(
                f"Service '{service_id}' in available_services does not exist in {SERVICES_FILE}. "
                f"Found in: {GRAPH_FILE} -> global_settings -> available_services"
            )

    service_price_ids = {sp.get("service_id") for sp in service_prices}
    for service_id in available_services:
        if service_id not in service_price_ids:
            results["warnings"].append(
                f"Service '{service_id}' is listed as available but has no row in {SERVICE_PRICES_FILE}"
            )

    run_validate_service_price_consistency(
        results, services=services, service_prices=service_prices
    )
