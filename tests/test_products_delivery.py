"""Branch coverage for scripts/validators/products_delivery.py."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

import scripts.data_files as data_files
from scripts.validators.products_delivery import validate_products_delivery

_WORKING_DAYS = {"weekdays": "mon_sat", "exclude_public_holidays": True}


def _delivery_domestic_next() -> list[dict]:
    return [{"zones": ["domestic"], "span": "next", "days_max": 1}]


def _write_minimal_bundle(
    tmp_path,
    *,
    provider: str = "deutschepost",
    country: str = "DE",
    products: list[dict],
) -> None:
    (tmp_path / "providers.json").write_text(
        json.dumps(
            {
                "providers": {
                    provider: {
                        "label": provider,
                        "name": f"{provider} entity",
                        "country": country,
                        "mark_types": ["stamp"],
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "policy").mkdir(exist_ok=True)
    (tmp_path / "policy" / "markets.json").write_text(
        json.dumps(
            {
                "file_type": "markets",
                "markets": {country: {"currency": "EUR", "working_days": _WORKING_DAYS}},
            }
        ),
        encoding="utf-8",
    )
    prov_dir = tmp_path / "providers" / provider
    prov_dir.mkdir(parents=True)
    (prov_dir / "products.json").write_text(
        json.dumps(
            {
                "file_type": "products",
                "provider": provider,
                "unit": {"weight": "g"},
                "products": products,
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "mappings.json").write_text(
        json.dumps(
            {
                "mappings": {
                    "policy": {
                        "schemas/markets.schema.json": "policy/markets.json",
                    },
                    "formats": {},
                    "registry": {"schemas/providers.schema.json": "providers.json"},
                    "providers": {
                        provider: {
                            "schemas/products.schema.json": f"providers/{provider}/products.json",
                        }
                    },
                }
            }
        ),
        encoding="utf-8",
    )


class TestValidateProductsDeliveryRealTree:
    def test_real_tree_passes(self) -> None:
        assert validate_products_delivery() == 0


class TestValidateProductsDeliveryBranches:
    def test_missing_delivery(self, tmp_path, capsys) -> None:
        _write_minimal_bundle(
            tmp_path,
            products=[
                {
                    "id": "standardbrief",
                    "zones": ["domestic"],
                }
            ],
        )
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            assert validate_products_delivery() == 1
        assert "delivery must be a non-empty array" in capsys.readouterr().out

    def test_zone_partition_missing(self, tmp_path, capsys) -> None:
        _write_minimal_bundle(
            tmp_path,
            products=[
                {
                    "id": "standardbrief",
                    "zones": ["domestic", "world"],
                    "delivery": _delivery_domestic_next(),
                }
            ],
        )
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            assert validate_products_delivery() == 1
        assert "delivery missing zones ['world']" in capsys.readouterr().out

    def test_zone_overlap_across_entries(self, tmp_path, capsys) -> None:
        _write_minimal_bundle(
            tmp_path,
            products=[
                {
                    "id": "standardbrief",
                    "zones": ["domestic"],
                    "delivery": [
                        {"zones": ["domestic"], "span": "next", "days_max": 1},
                        {"zones": ["domestic"], "span": "within", "days_max": 2},
                    ],
                }
            ],
        )
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            assert validate_products_delivery() == 1
        out = capsys.readouterr().out
        assert "appear in more than one delivery entry" in out

    def test_invalid_span_and_days(self, tmp_path, capsys) -> None:
        _write_minimal_bundle(
            tmp_path,
            products=[
                {
                    "id": "standardbrief",
                    "zones": ["domestic"],
                    "delivery": [
                        {"zones": ["domestic"], "span": "next", "days_max": 2, "days_min": 1},
                    ],
                }
            ],
        )
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            assert validate_products_delivery() == 1
        out = capsys.readouterr().out
        assert "span next requires days_max === 1" in out
        assert "span next must not include days_min" in out

    def test_between_requires_days_min(self, tmp_path, capsys) -> None:
        _write_minimal_bundle(
            tmp_path,
            products=[
                {
                    "id": "standardbrief",
                    "zones": ["domestic"],
                    "delivery": [
                        {"zones": ["domestic"], "span": "between", "days_max": 3},
                    ],
                }
            ],
        )
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            assert validate_products_delivery() == 1
        assert "span between requires days_min" in capsys.readouterr().out

    def test_between_days_min_gt_max(self, tmp_path, capsys) -> None:
        _write_minimal_bundle(
            tmp_path,
            products=[
                {
                    "id": "standardbrief",
                    "zones": ["domestic"],
                    "delivery": [
                        {
                            "zones": ["domestic"],
                            "span": "between",
                            "days_min": 5,
                            "days_max": 2,
                        },
                    ],
                }
            ],
        )
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            assert validate_products_delivery() == 1
        assert "days_min must be <= days_max" in capsys.readouterr().out

    def test_unknown_zone_in_delivery_entry(self, tmp_path, capsys) -> None:
        _write_minimal_bundle(
            tmp_path,
            products=[
                {
                    "id": "standardbrief",
                    "zones": ["domestic"],
                    "delivery": [
                        {"zones": ["world"], "span": "within", "days_max": 5},
                    ],
                }
            ],
        )
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            assert validate_products_delivery() == 1
        out = capsys.readouterr().out
        assert "is not in product.zones" in out

    def test_swisspost_b_post_requires_mon_fri(self, tmp_path, capsys) -> None:
        _write_minimal_bundle(
            tmp_path,
            provider="swisspost",
            country="CH",
            products=[
                {
                    "id": "b_post_standardbrief",
                    "zones": ["domestic"],
                    "delivery": [
                        {"zones": ["domestic"], "span": "within", "days_max": 3},
                    ],
                }
            ],
        )
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            assert validate_products_delivery() == 1
        assert "b_post_* domestic delivery must set weekdays mon_fri" in capsys.readouterr().out

    def test_swisspost_a_post_no_weekdays_override(self, tmp_path, capsys) -> None:
        _write_minimal_bundle(
            tmp_path,
            provider="swisspost",
            country="CH",
            products=[
                {
                    "id": "a_post_standardbrief",
                    "zones": ["domestic"],
                    "delivery": [
                        {
                            "zones": ["domestic"],
                            "span": "next",
                            "days_max": 1,
                            "weekdays": "mon_fri",
                        },
                    ],
                }
            ],
        )
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            assert validate_products_delivery() == 1
        assert "a_post_* must not override weekdays" in capsys.readouterr().out

    def test_missing_products_file(self, tmp_path, capsys) -> None:
        _write_minimal_bundle(
            tmp_path,
            products=[{"id": "x", "zones": ["domestic"], "delivery": _delivery_domestic_next()}],
        )
        (tmp_path / "providers" / "deutschepost" / "products.json").unlink()
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            assert validate_products_delivery() == 1
        assert "products.json" in capsys.readouterr().out

    def test_products_not_array(self, tmp_path, capsys) -> None:
        _write_minimal_bundle(
            tmp_path,
            products=[{"id": "x", "zones": ["domestic"], "delivery": _delivery_domestic_next()}],
        )
        (tmp_path / "providers" / "deutschepost" / "products.json").write_text(
            json.dumps({"file_type": "products", "provider": "deutschepost", "products": "bad"}),
            encoding="utf-8",
        )
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            assert validate_products_delivery() == 1
        assert "missing products array" in capsys.readouterr().out

    def test_provider_without_country(self, tmp_path, capsys, monkeypatch) -> None:
        monkeypatch.setattr(
            "scripts.validators.products_delivery.load_providers_registry",
            lambda: {"providers": {"deutschepost": {"label": "x"}}},
        )
        monkeypatch.setattr(
            "scripts.validators.products_delivery.list_provider_ids",
            lambda: ["deutschepost"],
        )
        assert validate_products_delivery() == 1
        assert "no country in providers.json" in capsys.readouterr().out

    def test_invalid_entry_type(self, tmp_path, capsys) -> None:
        _write_minimal_bundle(
            tmp_path,
            products=[
                {
                    "id": "standardbrief",
                    "zones": ["domestic"],
                    "delivery": ["bad"],
                }
            ],
        )
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            assert validate_products_delivery() == 1
        assert "delivery[0]: must be an object" in capsys.readouterr().out

    def test_within_must_not_have_days_min(self, tmp_path, capsys) -> None:
        _write_minimal_bundle(
            tmp_path,
            products=[
                {
                    "id": "standardbrief",
                    "zones": ["domestic"],
                    "delivery": [
                        {
                            "zones": ["domestic"],
                            "span": "within",
                            "days_max": 3,
                            "days_min": 1,
                        },
                    ],
                }
            ],
        )
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            assert validate_products_delivery() == 1
        assert "span within must not include days_min" in capsys.readouterr().out

    def test_invalid_weekdays(self, tmp_path, capsys) -> None:
        _write_minimal_bundle(
            tmp_path,
            products=[
                {
                    "id": "standardbrief",
                    "zones": ["domestic"],
                    "delivery": [
                        {
                            "zones": ["domestic"],
                            "span": "within",
                            "days_max": 3,
                            "weekdays": "sun_only",
                        },
                    ],
                }
            ],
        )
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            assert validate_products_delivery() == 1
        assert "weekdays must be one of" in capsys.readouterr().out

    def test_product_zones_not_array(self, tmp_path, capsys) -> None:
        _write_minimal_bundle(
            tmp_path,
            products=[
                {
                    "id": "standardbrief",
                    "zones": "domestic",
                    "delivery": _delivery_domestic_next(),
                }
            ],
        )
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            assert validate_products_delivery() == 1
        assert "zones must be an array" in capsys.readouterr().out

    def test_empty_zones_in_entry(self, tmp_path, capsys) -> None:
        _write_minimal_bundle(
            tmp_path,
            products=[
                {
                    "id": "standardbrief",
                    "zones": ["domestic"],
                    "delivery": [{"zones": [], "span": "next", "days_max": 1}],
                }
            ],
        )
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            assert validate_products_delivery() == 1
        assert "zones must be a non-empty array" in capsys.readouterr().out

    def test_duplicate_zone_within_entry(self, tmp_path, capsys) -> None:
        _write_minimal_bundle(
            tmp_path,
            products=[
                {
                    "id": "standardbrief",
                    "zones": ["domestic"],
                    "delivery": [
                        {"zones": ["domestic", "domestic"], "span": "next", "days_max": 1},
                    ],
                }
            ],
        )
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            assert validate_products_delivery() == 1
        assert "duplicate zone" in capsys.readouterr().out

    def test_invalid_days_max(self, tmp_path, capsys) -> None:
        _write_minimal_bundle(
            tmp_path,
            products=[
                {
                    "id": "standardbrief",
                    "zones": ["domestic"],
                    "delivery": [{"zones": ["domestic"], "span": "within", "days_max": 0}],
                }
            ],
        )
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            assert validate_products_delivery() == 1
        assert "days_max must be an integer >= 1" in capsys.readouterr().out

    def test_invalid_span_value(self, tmp_path, capsys) -> None:
        _write_minimal_bundle(
            tmp_path,
            products=[
                {
                    "id": "standardbrief",
                    "zones": ["domestic"],
                    "delivery": [{"zones": ["domestic"], "span": "soon", "days_max": 1}],
                }
            ],
        )
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            assert validate_products_delivery() == 1
        assert "span must be one of" in capsys.readouterr().out

    def test_non_string_zone_id(self, tmp_path, capsys) -> None:
        _write_minimal_bundle(
            tmp_path,
            products=[
                {
                    "id": "standardbrief",
                    "zones": ["domestic"],
                    "delivery": [{"zones": [1], "span": "next", "days_max": 1}],
                }
            ],
        )
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            assert validate_products_delivery() == 1
        out = capsys.readouterr().out
        assert "zone ids must be strings" in out

    def test_swisspost_b_post_skips_non_dict_entry_in_rule(self, tmp_path, capsys) -> None:
        _write_minimal_bundle(
            tmp_path,
            provider="swisspost",
            country="CH",
            products=[
                {
                    "id": "b_post_standardbrief",
                    "zones": ["domestic"],
                    "delivery": [
                        "skip",
                        {
                            "zones": ["domestic"],
                            "span": "within",
                            "days_max": 3,
                            "weekdays": "mon_fri",
                        },
                    ],
                }
            ],
        )
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            assert validate_products_delivery() == 1
        assert "delivery[0]: must be an object" in capsys.readouterr().out

    def test_provider_countries_not_dict(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr(
            "scripts.validators.products_delivery.load_providers_registry",
            lambda: {"providers": "bad"},
        )
        monkeypatch.setattr(
            "scripts.validators.products_delivery.list_provider_ids",
            lambda: [],
        )
        assert validate_products_delivery() == 0
