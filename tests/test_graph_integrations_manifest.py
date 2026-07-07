"""Cross-file checks for integrations.json vs graph.edges.wire."""

from __future__ import annotations

from scripts.validators.base import ValidationResults
from scripts.validators.graph.integrations_manifest import run_validate_integrations_manifest


def _results() -> ValidationResults:
    return {"errors": [], "warnings": [], "fixes_needed": [], "correct": []}


def _graph(*, provider: str = "acmepost", wire: dict | None = None, **overrides: object) -> dict:
    base = {
        "provider": provider,
        "dependencies": {
            "integrations": {
                "file": "integrations.json",
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


def _manifest(*, provider: str = "acmepost", adapter: str = "checkout_api") -> dict:
    return {
        "file_type": "integrations",
        "provider": provider,
        "adapter": adapter,
        "capabilities": ["mark_purchase_sync"],
    }


class TestIntegrationsManifest:
    def test_adapter_must_match_wire_key(self) -> None:
        r = _results()
        run_validate_integrations_manifest(
            r,
            graph=_graph(),
            integrations=_manifest(),
            provider_id="acmepost",
        )
        assert r["errors"] == []
        assert any("matches edges.wire" in item for item in r["correct"])

    def test_unknown_adapter_errors(self) -> None:
        r = _results()
        run_validate_integrations_manifest(
            r,
            graph=_graph(),
            integrations=_manifest(adapter="other_api"),
            provider_id="acmepost",
        )
        assert any("must match a key in" in e for e in r["errors"])

    def test_missing_file_with_dependency_errors(self) -> None:
        r = _results()
        run_validate_integrations_manifest(
            r,
            graph=_graph(),
            integrations=None,
            provider_id="acmepost",
        )
        assert any("file is missing" in e for e in r["errors"])

    def test_wire_without_manifest_warns_only(self) -> None:
        r = _results()
        run_validate_integrations_manifest(
            r,
            graph={
                "provider": "acmepost",
                "edges": {
                    "products": {},
                    "marks": {},
                    "wire": {"future_api": {"letter": {"domestic": {"base": 1}}}},
                },
            },
            integrations=None,
            provider_id="acmepost",
        )
        assert r["errors"] == []
        assert any("optional until an SDK adapter ships" in w for w in r["warnings"])

    def test_manifest_without_dependency_warns(self) -> None:
        r = _results()
        run_validate_integrations_manifest(
            r,
            graph={
                "provider": "acmepost",
                "edges": {
                    "products": {},
                    "marks": {},
                    "wire": {"checkout_api": {"letter": {"domestic": {"base": 1}}}},
                },
            },
            integrations=_manifest(),
            provider_id="acmepost",
        )
        assert any("dependencies.integrations is missing" in w for w in r["warnings"])
