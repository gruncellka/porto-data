"""Validation for ``graph.edges.wire`` adapter catalog codes."""

from __future__ import annotations

from typing import Any

from scripts.data_files import GRAPH_FILE, PRODUCTS_FILE, SERVICES_FILE
from scripts.validators.base import ValidationResults

from .edge_access import product_edges, validate_edges_container, wire_edges


def run_validate_strategy(
    results: ValidationResults,
    *,
    graph: dict[str, Any] | None,
) -> None:
    if not graph or not isinstance(graph, dict):
        return
    strategy = graph.get("strategy")
    allowed = {"service", "id", "speed", "min"}
    if strategy not in allowed:
        results["errors"].append(f"{GRAPH_FILE}: strategy must be one of {sorted(allowed)}")
    else:
        results["correct"].append(f"strategy: {strategy}")


def run_validate_no_entity_wire_codes(
    results: ValidationResults,
    *,
    products: list[dict[str, Any]],
    services: list[dict[str, Any]],
) -> None:
    for product in products:
        pid = product.get("id", "?")
        if "native_id" in product:
            results["errors"].append(
                f"{PRODUCTS_FILE}: product '{pid}' must not define native_id; use graph.edges.wire"
            )
        if "zone_native_ids" in product:
            results["errors"].append(
                f"{PRODUCTS_FILE}: product '{pid}' must not define zone_native_ids; "
                "use graph.edges.wire"
            )
    for service in services:
        sid = service.get("id", "?")
        if "native_id" in service:
            results["errors"].append(
                f"{SERVICES_FILE}: service '{sid}' must not define native_id; use graph.edges.wire"
            )
        if "product_native_ids" in service:
            results["errors"].append(
                f"{SERVICES_FILE}: service '{sid}' must not define product_native_ids; "
                "use graph.edges.wire"
            )


def run_validate_wire_edges(
    results: ValidationResults,
    *,
    graph: dict[str, Any] | None,
    product_dict: dict[str, dict[str, Any]],
    services_by_id: dict[str, dict[str, Any]],
    graph_service_ids: set[str],
) -> None:
    if not validate_edges_container(results, graph=graph):
        return
    if graph is None:
        return

    wire_root = wire_edges(graph)
    if not wire_root:
        results["warnings"].append(f"{GRAPH_FILE}: edges.wire is empty or omitted")
        return

    strategy = graph.get("strategy")
    product_links = product_edges(graph)

    for integration, products_wire in wire_root.items():
        if not isinstance(products_wire, dict):
            results["errors"].append(f"{GRAPH_FILE}: edges.wire.{integration} must be an object")
            continue
        for product_id, zones_wire in products_wire.items():
            if product_id not in product_dict:
                results["errors"].append(
                    f"{GRAPH_FILE}: wire product '{product_id}' unknown in products.json"
                )
                continue
            if product_id not in product_links:
                results["errors"].append(
                    f"{GRAPH_FILE}: wire product '{product_id}' missing from edges.products"
                )
                continue
            allowed_zones = set(product_links[product_id].get("zones") or [])
            if not isinstance(zones_wire, dict):
                continue
            for zone_id, zone_entry in zones_wire.items():
                if zone_id not in allowed_zones:
                    results["errors"].append(
                        f"{GRAPH_FILE}: wire.{integration}.{product_id}.{zone_id} "
                        f"not in edges.products zones {sorted(allowed_zones)}"
                    )
                if not isinstance(zone_entry, dict):
                    continue
                base = zone_entry.get("base")
                if base is None:
                    if strategy == "service" and integration == "internetmarke":
                        results["errors"].append(
                            f"{GRAPH_FILE}: wire.{integration}.{product_id}.{zone_id}.base "
                            "must not be null for service strategy"
                        )
                    else:
                        results["warnings"].append(
                            f"{GRAPH_FILE}: wire.{integration}.{product_id}.{zone_id}.base "
                            "is null (TBD catalog code)"
                        )
                elif strategy == "id" and base != product_id:
                    results["errors"].append(
                        f"{GRAPH_FILE}: wire.{integration}.{product_id}.{zone_id}.base "
                        f"must equal products.id {product_id!r} when strategy is id"
                    )
                svc_map = zone_entry.get("services") or {}
                if not isinstance(svc_map, dict):
                    continue
                for service_id in svc_map:
                    if service_id not in graph_service_ids:
                        results["errors"].append(
                            f"{GRAPH_FILE}: wire service '{service_id}' not in graph.services[]"
                        )
                    svc_row = services_by_id.get(service_id)
                    if svc_row is None:
                        results["errors"].append(
                            f"{GRAPH_FILE}: wire service '{service_id}' unknown in services.json"
                        )
                        continue
                    supported = svc_row.get("supported_zones")
                    if supported and zone_id not in supported:
                        results["errors"].append(
                            f"{GRAPH_FILE}: wire.{integration}.{product_id}.{zone_id} "
                            f"service '{service_id}' not in supported_zones {supported}"
                        )
