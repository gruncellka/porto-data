"""Cross-file checks for ``providers/<id>/integration.json`` (SDK execution manifest)."""

from __future__ import annotations

from typing import Any

from scripts.data_files import GRAPH_FILE, INTEGRATION_FILE
from scripts.validators.base import ValidationResults

from .edge_access import wire_integration_ids


def _integration_dependency(graph: dict[str, Any]) -> dict[str, Any] | None:
    dependencies = graph.get("dependencies")
    if not isinstance(dependencies, dict):
        return None
    entry = dependencies.get("integration")
    return entry if isinstance(entry, dict) else None


def run_validate_integration_manifest(
    results: ValidationResults,
    *,
    graph: dict[str, Any] | None,
    integration: dict[str, Any] | None,
    provider_id: str,
) -> None:
    """Align integration.json with graph.dependencies and graph.edges.wire."""
    if graph is None or not isinstance(graph, dict):
        return

    wire_ids = wire_integration_ids(graph)
    dependency = _integration_dependency(graph)
    has_manifest = integration is not None

    if dependency is not None:
        dep_file = dependency.get("file")
        if dep_file != INTEGRATION_FILE:
            results["errors"].append(
                f"{GRAPH_FILE}: dependencies.integration.file must be "
                f"{INTEGRATION_FILE!r}, got {dep_file!r}"
            )
        elif not has_manifest:
            results["errors"].append(
                f"{GRAPH_FILE}: dependencies.integration references "
                f"{INTEGRATION_FILE} but the file is missing"
            )
        else:
            results["correct"].append(f"dependencies.integration.file points at {INTEGRATION_FILE}")

    if not has_manifest:
        if dependency is not None:
            return
        if wire_ids:
            results["warnings"].append(
                f"{GRAPH_FILE}: edges.wire defines {sorted(wire_ids)} but "
                f"{INTEGRATION_FILE} is absent (optional until an SDK adapter ships)"
            )
        return

    manifest = integration
    if not isinstance(manifest, dict):
        return

    if dependency is None:
        results["warnings"].append(
            f"{INTEGRATION_FILE} exists but {GRAPH_FILE} dependencies.integration is missing"
        )

    adapter = manifest.get("adapter")
    if not isinstance(adapter, str) or not adapter.strip():
        results["errors"].append(f"{INTEGRATION_FILE}: adapter must be a non-empty string")
        return

    adapter_id = adapter.strip().lower()
    if adapter_id not in wire_ids:
        results["errors"].append(
            f"{INTEGRATION_FILE}: adapter {adapter_id!r} must match a key in "
            f"{GRAPH_FILE} edges.wire (have {sorted(wire_ids) or 'none'})"
        )
    else:
        results["correct"].append(f"integration.adapter {adapter_id!r} matches edges.wire")

    billing = manifest.get("billing") or []
    execution = manifest.get("execution") or []
    if not isinstance(billing, list) or not isinstance(execution, list):
        results["errors"].append(
            f"{INTEGRATION_FILE}: billing and execution must be arrays when present"
        )
        return
    if not billing and not execution:
        results["errors"].append(
            f"{INTEGRATION_FILE}: at least one billing or execution method must be declared"
        )
