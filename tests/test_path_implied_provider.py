"""Path-implied provider id helpers."""

from scripts.data_files import (
    provider_id_from_bundle_path,
    redundant_provider_field_error,
)


def test_provider_id_from_bundle_path() -> None:
    assert provider_id_from_bundle_path("providers/deutschepost/graph.json") == "deutschepost"
    assert provider_id_from_bundle_path("policy/markets.json") is None


def test_redundant_provider_field_error() -> None:
    assert (
        redundant_provider_field_error(
            "providers/deutschepost/products.json",
            {"file_type": "products", "provider": "deutschepost"},
        )
        == "providers/deutschepost/products.json: top-level 'provider' is path-implied by "
        "providers/<id>/ layout — remove redundant field"
    )
    assert redundant_provider_field_error("policy/markets.json", {"provider": "de"}) is None
    assert (
        redundant_provider_field_error(
            "providers/acme/integration.json", {"file_type": "integration"}
        )
        is None
    )
