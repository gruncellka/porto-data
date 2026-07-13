"""Cross-file checks for execution.json vs graph.edges.wire."""

from __future__ import annotations

from scripts.validators.base import ValidationResults
from scripts.validators.graph.execution_manifest import run_validate_execution_manifest


def _results() -> ValidationResults:
    return {"errors": [], "warnings": [], "fixes_needed": [], "correct": []}


def _graph(*, provider: str = "acmepost", wire: dict | None = None, **overrides: object) -> dict:
    base = {
        "provider": provider,
        "dependencies": {
            "execution": {
                "file": "execution.json",
                "depends_on": [],
                "description": "SDK execution manifest",
            }
        },
        "edges": {
            "products": {},
            "marks": {},
            "wire": wire
            if wire is not None
            else {"checkout_api": {"letter": {"domestic": {"base": "sku-1"}}}},
        },
    }
    base.update(overrides)
    return base


def _manifest(*, wire: str = "checkout_api") -> dict:
    return {
        "file_type": "execution",
        "wire": wire,
        "execution": ["create_mark"],
    }


class TestExecutionManifest:
    def test_wire_must_match_wire_key(self) -> None:
        r = _results()
        run_validate_execution_manifest(
            r,
            graph=_graph(),
            execution=_manifest(),
            provider_id="acmepost",
        )
        assert r["errors"] == []
        assert any("matches edges.wire" in item for item in r["correct"])

    def test_unknown_wire_errors(self) -> None:
        r = _results()
        run_validate_execution_manifest(
            r,
            graph=_graph(),
            execution=_manifest(wire="other_api"),
            provider_id="acmepost",
        )
        assert any("must match a key in" in e for e in r["errors"])

    def test_missing_file_with_dependency_errors(self) -> None:
        r = _results()
        run_validate_execution_manifest(
            r,
            graph=_graph(),
            execution=None,
            provider_id="acmepost",
        )
        assert any("file is missing" in e for e in r["errors"])

    def test_wire_without_manifest_warns_only(self) -> None:
        r = _results()
        run_validate_execution_manifest(
            r,
            graph={
                "provider": "acmepost",
                "edges": {
                    "products": {},
                    "marks": {},
                    "wire": {"future_api": {"letter": {"domestic": {"base": 1}}}},
                },
            },
            execution=None,
            provider_id="acmepost",
        )
        assert r["errors"] == []
        assert any("optional until an SDK adapter ships" in w for w in r["warnings"])

    def test_manifest_without_dependency_warns(self) -> None:
        r = _results()
        run_validate_execution_manifest(
            r,
            graph={
                "provider": "acmepost",
                "edges": {
                    "products": {},
                    "marks": {},
                    "wire": {"checkout_api": {"letter": {"domestic": {"base": 1}}}},
                },
            },
            execution=_manifest(),
            provider_id="acmepost",
        )
        assert any("dependencies.execution is missing" in w for w in r["warnings"])

    def test_graph_none_or_invalid_returns_early(self) -> None:
        r = _results()
        run_validate_execution_manifest(
            r, graph=None, execution=_manifest(), provider_id="acmepost"
        )
        assert r["errors"] == [] and r["warnings"] == []

        r2 = _results()
        run_validate_execution_manifest(
            r2, graph="not-a-graph", execution=_manifest(), provider_id="acmepost"
        )
        assert r2["errors"] == [] and r2["warnings"] == []

    def test_wrong_dependency_file_errors(self) -> None:
        r = _results()
        graph = _graph()
        graph["dependencies"]["execution"]["file"] = "wrong.json"
        run_validate_execution_manifest(
            r, graph=graph, execution=_manifest(), provider_id="acmepost"
        )
        assert any("dependencies.execution.file must be" in e for e in r["errors"])

    def test_execution_not_dict_returns_without_side_effects(self) -> None:
        r = _results()
        run_validate_execution_manifest(
            r,
            graph=_graph(),
            execution=[],  # type: ignore[arg-type]
            provider_id="acmepost",
        )
        assert r["errors"] == [] and r["warnings"] == []

    def test_empty_wire_errors(self) -> None:
        r = _results()
        run_validate_execution_manifest(
            r,
            graph=_graph(),
            execution=_manifest(wire="   "),
            provider_id="acmepost",
        )
        assert any("wire must be a non-empty string" in e for e in r["errors"])

    def test_empty_billing_and_execution_errors(self) -> None:
        r = _results()
        run_validate_execution_manifest(
            r,
            graph=_graph(),
            execution={
                "file_type": "execution",
                "wire": "checkout_api",
                "billing": [],
                "execution": [],
            },
            provider_id="acmepost",
        )
        assert any("at least one billing or execution method" in e for e in r["errors"])

    def test_non_array_billing_or_execution_errors(self) -> None:
        r = _results()
        run_validate_execution_manifest(
            r,
            graph=_graph(),
            execution={
                "file_type": "execution",
                "wire": "checkout_api",
                "billing": "get_wallet_balance",
                "execution": ["create_mark"],
            },
            provider_id="acmepost",
        )
        assert any("billing and execution must be arrays" in e for e in r["errors"])

    def test_dependency_file_pointer_correct(self) -> None:
        r = _results()
        run_validate_execution_manifest(
            r, graph=_graph(), execution=_manifest(), provider_id="acmepost"
        )
        assert any("points at execution.json" in c for c in r["correct"])
