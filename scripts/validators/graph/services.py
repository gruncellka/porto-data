"""``graph.services``, service price rows, and service reference helpers."""

from __future__ import annotations

from typing import Any

from scripts.data_files import GRAPH_FILE, SERVICE_PRICES_FILE, SERVICES_FILE, ZONES_FILE
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
    zone_ids: set[str] | None = None,
) -> None:
    """Validate ``graph.services`` catalog ids and service-price consistency."""
    attached = graph.get("services", [])

    valid_ids = service_ids_set(services)
    for sp in service_prices:
        sid = sp.get("service_id")
        if not sid:
            continue
        if str(sid) not in valid_ids:
            results["errors"].append(
                f"Service '{sid}' in service_prices does not exist in {SERVICES_FILE} "
                f"(catalog id required). Found in: {SERVICE_PRICES_FILE} -> service_prices"
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
    run_validate_service_price_zones(
        results,
        services=services,
        service_prices=service_prices,
        zone_ids=zone_ids or set(),
    )


def run_validate_service_price_zones(
    results: ValidationResults,
    *,
    services: dict[str, Any] | None,
    service_prices: list[dict[str, Any]],
    zone_ids: set[str],
) -> None:
    """Unzoned vs zoned encoding: never mix; zoned rows cover supported_zones."""
    by_sid: dict[str, list[dict[str, Any]]] = {}
    seen: set[tuple[str, str | None]] = set()
    for sp in service_prices:
        if not isinstance(sp, dict):
            continue
        sid = sp.get("service_id")
        if not sid:
            continue
        sid_str = str(sid)
        zone_raw = sp.get("zone")
        zone_key = str(zone_raw) if zone_raw else None
        key = (sid_str, zone_key)
        if key in seen:
            label = f"{sid_str}/{zone_key}" if zone_key else sid_str
            results["errors"].append(
                f"Duplicate service_prices key '{label}'. "
                f"Found in: {SERVICE_PRICES_FILE} -> service_prices"
            )
        seen.add(key)
        by_sid.setdefault(sid_str, []).append(sp)
        if zone_key and zone_ids and zone_key not in zone_ids:
            results["errors"].append(
                f"Service '{sid_str}' price zone '{zone_key}' is not in {ZONES_FILE}. "
                f"Found in: {SERVICE_PRICES_FILE} -> service_prices"
            )

    for sid, rows in by_sid.items():
        zoned = [row for row in rows if row.get("zone")]
        unzoned = [row for row in rows if not row.get("zone")]
        if zoned and unzoned:
            results["errors"].append(
                f"Service '{sid}' mixes unzoned and zoned service_prices rows. "
                f"Use one unzoned amount or one row per supported zone. "
                f"Found in: {SERVICE_PRICES_FILE} -> service_prices"
            )
            continue
        if len(unzoned) > 1:
            results["errors"].append(
                f"Service '{sid}' has more than one unzoned service_prices row. "
                f"Found in: {SERVICE_PRICES_FILE} -> service_prices"
            )
            continue
        if not zoned:
            continue
        service = get_service_by_id(services, sid)
        supported = {str(z) for z in ((service or {}).get("supported_zones") or []) if z}
        priced = {str(row.get("zone")) for row in zoned}
        missing = supported - priced
        extra = priced - supported
        if missing:
            results["errors"].append(
                f"Service '{sid}' is zoned but missing service_prices for "
                f"{sorted(missing)}. Found in: {SERVICE_PRICES_FILE} -> service_prices"
            )
        if extra:
            results["errors"].append(
                f"Service '{sid}' has service_prices zones {sorted(extra)} "
                f"not in services[].supported_zones. "
                f"Found in: {SERVICE_PRICES_FILE} -> service_prices"
            )
