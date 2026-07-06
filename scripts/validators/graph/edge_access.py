"""Access ``graph.json`` ``edges.products`` and ``edges.marks``."""

from __future__ import annotations

from typing import Any

from scripts.data_files import GRAPH_FILE
from scripts.validators.base import ValidationResults


def _edges_root(graph: dict[str, Any] | None) -> dict[str, Any] | None:
    if not graph or not isinstance(graph, dict):
        return None
    edges = graph.get("edges")
    return edges if isinstance(edges, dict) else None


def product_edges(graph: dict[str, Any] | None) -> dict[str, Any]:
    root = _edges_root(graph)
    if root is None:
        return {}
    products = root.get("products")
    return products if isinstance(products, dict) else {}


def mark_edges(graph: dict[str, Any] | None) -> dict[str, Any]:
    root = _edges_root(graph)
    if root is None:
        return {}
    marks = root.get("marks")
    return marks if isinstance(marks, dict) else {}


def wire_edges(graph: dict[str, Any] | None) -> dict[str, Any]:
    root = _edges_root(graph)
    if root is None:
        return {}
    wire = root.get("wire")
    return wire if isinstance(wire, dict) else {}


def validate_edges_container(results: ValidationResults, *, graph: dict[str, Any] | None) -> bool:
    """Ensure ``edges`` has ``products`` and ``marks`` objects. Returns False if invalid."""
    if graph is None or not isinstance(graph, dict):
        return False
    if graph.get("mark_edges") is not None:
        results["errors"].append(
            f"{GRAPH_FILE}: mark_edges is removed; use edges.marks under edges"
        )
        return False
    root = _edges_root(graph)
    if root is None:
        results["errors"].append(f"{GRAPH_FILE}: edges must be an object")
        return False
    ok = True
    products = root.get("products")
    if not isinstance(products, dict):
        results["errors"].append(f"{GRAPH_FILE}: edges.products must be an object")
        ok = False
    marks = root.get("marks")
    if not isinstance(marks, dict):
        results["errors"].append(f"{GRAPH_FILE}: edges.marks must be an object")
        ok = False
    return ok
