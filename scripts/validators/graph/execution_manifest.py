"""Cross-file checks for ``providers/<id>/execution.json`` (SDK execution manifest)."""

from __future__ import annotations

from typing import Any

from scripts.data_files import EXECUTION_FILE, GRAPH_FILE
from scripts.validators.base import ValidationResults

from .edge_access import wire_integration_ids


def _execution_dependency(graph: dict[str, Any]) -> dict[str, Any] | None:
    dependencies = graph.get("dependencies")
    if not isinstance(dependencies, dict):
        return None
    entry = dependencies.get("execution")
    return entry if isinstance(entry, dict) else None


def run_validate_execution_manifest(
    results: ValidationResults,
    *,
    graph: dict[str, Any] | None,
    execution: dict[str, Any] | None,
    provider_id: str,
) -> None:
    """Align execution.json with graph.dependencies and graph.edges.wire."""
    if graph is None or not isinstance(graph, dict):
        return

    wire_ids = wire_integration_ids(graph)
    dependency = _execution_dependency(graph)
    has_manifest = execution is not None

    if dependency is not None:
        dep_file = dependency.get("file")
        if dep_file != EXECUTION_FILE:
            results["errors"].append(
                f"{GRAPH_FILE}: dependencies.execution.file must be "
                f"{EXECUTION_FILE!r}, got {dep_file!r}"
            )
        elif not has_manifest:
            results["errors"].append(
                f"{GRAPH_FILE}: dependencies.execution references "
                f"{EXECUTION_FILE} but the file is missing"
            )
        else:
            results["correct"].append(f"dependencies.execution.file points at {EXECUTION_FILE}")

    if not has_manifest:
        if dependency is not None:
            return
        if wire_ids:
            results["warnings"].append(
                f"{GRAPH_FILE}: edges.wire defines {sorted(wire_ids)} but "
                f"{EXECUTION_FILE} is absent (optional until an SDK adapter ships)"
            )
        return

    manifest = execution
    if not isinstance(manifest, dict):
        return

    if dependency is None:
        results["warnings"].append(
            f"{EXECUTION_FILE} exists but {GRAPH_FILE} dependencies.execution is missing"
        )

    wire = manifest.get("wire")
    if not isinstance(wire, str) or not wire.strip():
        results["errors"].append(f"{EXECUTION_FILE}: wire must be a non-empty string")
        return

    wire_id = wire.strip().lower()
    if wire_id not in wire_ids:
        results["errors"].append(
            f"{EXECUTION_FILE}: wire {wire_id!r} must match a key in "
            f"{GRAPH_FILE} edges.wire (have {sorted(wire_ids) or 'none'})"
        )
    else:
        results["correct"].append(f"execution.wire {wire_id!r} matches edges.wire")

    billing = manifest.get("billing") or []
    execution_methods = manifest.get("execution") or []
    if not isinstance(billing, list) or not isinstance(execution_methods, list):
        results["errors"].append(
            f"{EXECUTION_FILE}: billing and execution must be arrays when present"
        )
        return
    if not billing and not execution_methods:
        results["errors"].append(
            f"{EXECUTION_FILE}: at least one billing or execution method must be declared"
        )
