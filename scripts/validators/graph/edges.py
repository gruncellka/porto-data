"""Validation for ``graph.edges`` and related catalog consistency."""

from __future__ import annotations

from typing import Any

from scripts.data_files import GRAPH_FILE, PRODUCTS_FILE, WEIGHTS_FILE, ZONES_FILE
from scripts.validators.base import ValidationResults


def run_validate_edges(
    results: ValidationResults,
    *,
    graph: dict[str, Any],
    product_dict: dict[str, dict[str, Any]],
    zone_ids: dict[str, dict[str, Any]],
    weight_tier_ids: set[str],
    product_prices: list[dict[str, Any]],
) -> None:
    edges = graph.get("edges", {})
    for product_id, edge_data in edges.items():
        _validate_product_edge(
            results,
            product_id,
            edge_data,
            product_dict=product_dict,
            zone_ids=zone_ids,
            weight_tier_ids=weight_tier_ids,
            product_prices=product_prices,
        )


def _validate_product_edge(
    results: ValidationResults,
    product_id: str,
    edge_data: dict[str, Any],
    *,
    product_dict: dict[str, dict[str, Any]],
    zone_ids: dict[str, dict[str, Any]],
    weight_tier_ids: set[str],
    product_prices: list[dict[str, Any]],
) -> None:
    if product_id not in product_dict:
        results["errors"].append(
            f"Product '{product_id}' in edges does not exist in {PRODUCTS_FILE}. "
            f"Found in: {GRAPH_FILE} -> edges -> {product_id}"
        )
        return

    product = product_dict[product_id]
    link_zones = set(edge_data.get("zones", []))
    link_weight_tiers = set(edge_data.get("weight_tiers", []))
    product_zones = set(product.get("zones", []))
    product_weight_tier = product.get("weight_tier")

    _validate_product_zones(results, product_id, link_zones, product_zones, zone_ids=zone_ids)
    _validate_product_weight_tiers(
        results,
        product_id,
        link_weight_tiers,
        product_weight_tier,
        weight_tier_ids=weight_tier_ids,
        product_prices=product_prices,
    )
    _validate_price_coverage(results, product_id, link_zones, link_weight_tiers, product_prices)


def _validate_product_zones(
    results: ValidationResults,
    product_id: str,
    link_zones: set[str],
    product_zones: set[str],
    *,
    zone_ids: dict[str, dict[str, Any]],
) -> None:
    for zone in link_zones:
        if zone not in zone_ids:
            results["errors"].append(
                f"Zone '{zone}' for product '{product_id}' does not exist in {ZONES_FILE}. "
                f"Found in: {GRAPH_FILE} -> edges -> {product_id} -> zones"
            )

    if link_zones == product_zones:
        results["correct"].append(f"Product '{product_id}': zones match ({sorted(link_zones)})")
    else:
        results["fixes_needed"].append(
            f"Product '{product_id}': zones mismatch - edges: {sorted(link_zones)}, "
            f"product: {sorted(product_zones)}"
        )


def _validate_product_weight_tiers(
    results: ValidationResults,
    product_id: str,
    link_weight_tiers: set[str],
    product_weight_tier: str | None,
    *,
    weight_tier_ids: set[str],
    product_prices: list[dict[str, Any]],
) -> None:
    for wt in link_weight_tiers:
        if wt not in weight_tier_ids:
            results["errors"].append(
                f"Weight tier '{wt}' for product '{product_id}' does not exist in {WEIGHTS_FILE}. "
                f"Found in: {GRAPH_FILE} -> edges -> {product_id} -> weight_tiers"
            )

    price_weight_tiers = {
        p["weight_tier"] for p in product_prices if p.get("product_id") == product_id
    }

    if product_weight_tier and product_weight_tier in link_weight_tiers:
        results["correct"].append(
            f"Product '{product_id}': weight_tier '{product_weight_tier}' is in edges"
        )
    elif product_weight_tier:
        results["fixes_needed"].append(
            f"Product '{product_id}': weight_tier '{product_weight_tier}' from product "
            f"not in edges {sorted(link_weight_tiers)}"
        )

    missing_tiers = price_weight_tiers - link_weight_tiers
    if missing_tiers:
        results["fixes_needed"].append(
            f"Product '{product_id}': prices exist for weight_tiers {sorted(missing_tiers)} but not in edges"
        )
    elif price_weight_tiers == link_weight_tiers:
        results["correct"].append(
            f"Product '{product_id}': all price weight_tiers match edges ({sorted(price_weight_tiers)})"
        )


def _validate_price_coverage(
    results: ValidationResults,
    product_id: str,
    link_zones: set[str],
    link_weight_tiers: set[str],
    product_prices: list[dict[str, Any]],
) -> None:
    for zone in link_zones:
        for weight_tier in link_weight_tiers:
            matching_price = any(
                p.get("product_id") == product_id
                and p.get("zone") == zone
                and p.get("weight_tier") == weight_tier
                for p in product_prices
            )
            if not matching_price:
                results["warnings"].append(
                    f"No price found for product '{product_id}', zone '{zone}', weight_tier '{weight_tier}'"
                )


def run_validate_products_in_edges(
    results: ValidationResults,
    *,
    graph: dict[str, Any],
    product_dict: dict[str, dict[str, Any]],
) -> None:
    edges = graph.get("edges", {})
    products_in_data = set(product_dict.keys())
    products_in_edges = set(edges.keys())
    missing_products = products_in_data - products_in_edges

    if missing_products:
        results["fixes_needed"].append(
            f"Products in products.json but not in edges: {sorted(missing_products)}"
        )
    else:
        results["correct"].append("All products are in edges")


def run_validate_zones_and_weight_tiers_in_edges(
    results: ValidationResults,
    *,
    graph: dict[str, Any],
    zone_ids: dict[str, dict[str, Any]],
    weight_tier_ids: set[str],
) -> None:
    edges = graph.get("edges", {})

    all_link_zones: set[str] = set()
    all_link_weight_tiers: set[str] = set()
    for edge_data in edges.values():
        all_link_zones.update(edge_data.get("zones", []))
        all_link_weight_tiers.update(edge_data.get("weight_tiers", []))

    invalid_zones = all_link_zones - set(zone_ids.keys())
    if not invalid_zones:
        results["correct"].append("All zones in edges are valid")

    invalid_weight_tiers = all_link_weight_tiers - weight_tier_ids
    if not invalid_weight_tiers:
        results["correct"].append("All weight_tiers in edges are valid")
