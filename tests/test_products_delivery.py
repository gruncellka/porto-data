"""Branch coverage for scripts/validators/products_delivery.py."""

from __future__ import annotations

import json
from unittest.mock import patch

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


def _write_laposte_bundle(
    tmp_path,
    *,
    products: list[dict],
    graph_products: dict | None = None,
) -> None:
    _write_minimal_bundle(
        tmp_path,
        provider="laposte",
        country="FR",
        products=products,
    )
    prov_dir = tmp_path / "providers" / "laposte"
    (prov_dir / "features.json").write_text(
        json.dumps(
            {
                "file_type": "features",
                "provider": "laposte",
                "features": [
                    {
                        "id": "numero_suivi",
                        "porto_id": "tracking_number",
                        "name": "Suivi",
                        "label": "Tracking",
                        "description": "Tracking",
                    },
                    {
                        "id": "preuve_depot",
                        "porto_id": "proof_of_mailing",
                        "name": "Depot",
                        "label": "Depot",
                        "description": "Depot",
                    },
                    {
                        "id": "signature_destinataire",
                        "porto_id": "recipient_signature",
                        "name": "Sig",
                        "label": "Sig",
                        "description": "Sig",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    edges = graph_products or {
        pid: {"zones": p.get("zones", []), "weight_tiers": ["W0020"]}
        for pid, p in ((str(x["id"]), x) for x in products if isinstance(x, dict))
    }
    (prov_dir / "graph.json").write_text(
        json.dumps(
            {
                "file_type": "graph",
                "provider": "laposte",
                "edges": {"products": edges},
            }
        ),
        encoding="utf-8",
    )
    mappings_path = tmp_path / "mappings.json"
    mappings = json.loads(mappings_path.read_text(encoding="utf-8"))
    mappings["mappings"]["providers"]["laposte"].update(
        {
            "schemas/features.schema.json": "providers/laposte/features.json",
            "schemas/graph.schema.json": "providers/laposte/graph.json",
        }
    )
    mappings_path.write_text(json.dumps(mappings), encoding="utf-8")


class TestProductsIndemnityAndFeatures:
    def test_invalid_included_feature_ref(self, tmp_path, capsys) -> None:
        _write_laposte_bundle(
            tmp_path,
            products=[
                {
                    "id": "lettre_verte_suivie",
                    "porto_id": "small",
                    "zones": ["domestic"],
                    "included_features": ["missing_feat"],
                    "delivery": [{"zones": ["domestic"], "span": "within", "days_max": 3}],
                }
            ],
        )
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            assert validate_products_delivery() == 1
        assert "not found in providers/laposte/features.json" in capsys.readouterr().out

    def test_recommandee_requires_indemnity(self, tmp_path, capsys) -> None:
        _write_laposte_bundle(
            tmp_path,
            products=[
                {
                    "id": "lettre_recommandee_r_un",
                    "porto_id": "small",
                    "zones": ["domestic"],
                    "delivery": [
                        {"zones": ["domestic"], "span": "between", "days_min": 1, "days_max": 2}
                    ],
                }
            ],
        )
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            assert validate_products_delivery() == 1
        assert "must include indemnity" in capsys.readouterr().out

    def test_non_recommandee_must_not_have_indemnity(self, tmp_path, capsys) -> None:
        _write_laposte_bundle(
            tmp_path,
            products=[
                {
                    "id": "lettre_verte",
                    "porto_id": "small",
                    "zones": ["domestic"],
                    "indemnity": {
                        "tier": "R1",
                        "max": {"amount": 1600},
                    },
                    "delivery": [{"zones": ["domestic"], "span": "within", "days_max": 3}],
                }
            ],
        )
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            assert validate_products_delivery() == 1
        assert "only lettre_recommandee_*" in capsys.readouterr().out

    def test_wrong_indemnity_tier(self, tmp_path, capsys) -> None:
        _write_laposte_bundle(
            tmp_path,
            products=[
                {
                    "id": "lettre_recommandee_r_deux",
                    "porto_id": "small",
                    "zones": ["domestic"],
                    "indemnity": {
                        "tier": "R1",
                        "max": {"amount": 15300},
                    },
                    "delivery": [
                        {"zones": ["domestic"], "span": "between", "days_min": 1, "days_max": 2}
                    ],
                }
            ],
        )
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            assert validate_products_delivery() == 1
        assert "indemnity.tier must be 'R2'" in capsys.readouterr().out

    def test_twin_identical_fingerprint_fails(self, tmp_path, capsys) -> None:
        delivery = [{"zones": ["domestic"], "span": "within", "days_max": 3}]
        _write_laposte_bundle(
            tmp_path,
            products=[
                {
                    "id": "prod_a",
                    "porto_id": "small",
                    "zones": ["domestic"],
                    "tracking_mode": "optional",
                    "delivery": delivery,
                },
                {
                    "id": "prod_b",
                    "porto_id": "small",
                    "zones": ["domestic"],
                    "tracking_mode": "optional",
                    "delivery": delivery,
                },
            ],
            graph_products={
                "prod_a": {"zones": ["domestic"], "weight_tiers": ["W0020"]},
                "prod_b": {"zones": ["domestic"], "weight_tiers": ["W0020"]},
            },
        )
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            assert validate_products_delivery() == 1
        assert "identical resolution fingerprint" in capsys.readouterr().out

    def test_included_features_not_array(self, tmp_path, capsys) -> None:
        _write_laposte_bundle(
            tmp_path,
            products=[
                {
                    "id": "lettre_verte_suivie",
                    "porto_id": "small",
                    "zones": ["domestic"],
                    "included_features": "bad",
                    "delivery": [{"zones": ["domestic"], "span": "within", "days_max": 3}],
                }
            ],
        )
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            assert validate_products_delivery() == 1
        assert "included_features must be an array" in capsys.readouterr().out

    def test_indemnity_invalid_amount(self, tmp_path, capsys) -> None:
        _write_laposte_bundle(
            tmp_path,
            products=[
                {
                    "id": "lettre_recommandee_r_un",
                    "porto_id": "small",
                    "zones": ["domestic"],
                    "indemnity": {"tier": "R1", "max": {"amount": 0}},
                    "delivery": [
                        {"zones": ["domestic"], "span": "between", "days_min": 1, "days_max": 2}
                    ],
                }
            ],
        )
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            assert validate_products_delivery() == 1
        assert "indemnity.max.amount must be an integer >= 1" in capsys.readouterr().out

    def test_delivery_zone_signature_none(self) -> None:
        from scripts.validators.products_delivery import _delivery_zone_signature

        assert _delivery_zone_signature({"delivery": "bad"}, "domestic") is None
        assert (
            _delivery_zone_signature(
                {"delivery": [{"zones": ["world"], "span": "within", "days_max": 1}]},
                "domestic",
            )
            is None
        )
        assert _delivery_zone_signature(
            {"delivery": ["skip", {"zones": ["domestic"], "span": "next", "days_max": 1}]},
            "domestic",
        ) == ("next", None, 1, None)

    def test_included_features_non_string_and_duplicate(self, tmp_path, capsys) -> None:
        _write_laposte_bundle(
            tmp_path,
            products=[
                {
                    "id": "lettre_verte_suivie",
                    "porto_id": "small",
                    "zones": ["domestic"],
                    "included_features": ["numero_suivi", 1, "numero_suivi"],
                    "delivery": [{"zones": ["domestic"], "span": "within", "days_max": 3}],
                }
            ],
        )
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            assert validate_products_delivery() == 1
        out = capsys.readouterr().out
        assert "included_features entries must be strings" in out
        assert "duplicate included_features entry 'numero_suivi'" in out

    def test_indemnity_not_object(self, tmp_path, capsys) -> None:
        _write_minimal_bundle(
            tmp_path,
            products=[
                {
                    "id": "standardbrief",
                    "zones": ["domestic"],
                    "indemnity": "bad",
                    "delivery": _delivery_domestic_next(),
                }
            ],
        )
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            assert validate_products_delivery() == 1
        assert "indemnity must be an object" in capsys.readouterr().out

    def test_indemnity_empty_tier(self, tmp_path, capsys) -> None:
        _write_laposte_bundle(
            tmp_path,
            products=[
                {
                    "id": "lettre_recommandee_r_un",
                    "porto_id": "small",
                    "zones": ["domestic"],
                    "indemnity": {"tier": "", "max": {"amount": 1600, "currency": "EUR"}},
                    "delivery": [
                        {"zones": ["domestic"], "span": "between", "days_min": 1, "days_max": 2}
                    ],
                }
            ],
        )
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            assert validate_products_delivery() == 1
        assert "indemnity.tier must be a non-empty string" in capsys.readouterr().out

    def test_indemnity_max_not_object(self, tmp_path, capsys) -> None:
        _write_laposte_bundle(
            tmp_path,
            products=[
                {
                    "id": "lettre_recommandee_r_un",
                    "porto_id": "small",
                    "zones": ["domestic"],
                    "indemnity": {"tier": "R1", "max": "bad"},
                    "delivery": [
                        {"zones": ["domestic"], "span": "between", "days_min": 1, "days_max": 2}
                    ],
                }
            ],
        )
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            assert validate_products_delivery() == 1
        assert "indemnity.max must be an object" in capsys.readouterr().out

    def test_non_dict_product_skipped(self, tmp_path, capsys) -> None:
        _write_laposte_bundle(
            tmp_path,
            products=[
                "skip",
                {
                    "id": "lettre_verte",
                    "porto_id": "small",
                    "zones": ["domestic"],
                    "delivery": [{"zones": ["domestic"], "span": "within", "days_max": 3}],
                },
            ],
        )
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            assert validate_products_delivery() == 0

    def test_twin_guard_skips_bad_graph_edges(self, tmp_path, capsys) -> None:
        delivery = [{"zones": ["domestic"], "span": "within", "days_max": 3}]
        _write_laposte_bundle(
            tmp_path,
            products=[
                {
                    "id": "prod_a",
                    "porto_id": "small",
                    "zones": ["domestic"],
                    "tracking_mode": "optional",
                    "delivery": delivery,
                },
                {
                    "id": "prod_b",
                    "porto_id": "small",
                    "zones": ["domestic"],
                    "tracking_mode": "included",
                    "delivery": delivery,
                },
            ],
            graph_products={
                "missing_product": {"zones": ["domestic"], "weight_tiers": ["W0020"]},
                "prod_a": {"zones": ["domestic"], "weight_tiers": ["W0020"]},
                "prod_b": {"zones": ["domestic"], "weight_tiers": ["W0020"]},
                "no_porto": {"zones": ["domestic"], "weight_tiers": ["W0020"]},
                "bad_zones": {"zones": "domestic", "weight_tiers": ["W0020"]},
                "bad_tiers": {"zones": ["domestic"], "weight_tiers": "W0020"},
                "bad_zone_type": {"zones": [1], "weight_tiers": ["W0020"]},
                "bad_tier_type": {"zones": ["domestic"], "weight_tiers": [1]},
            },
        )
        products_path = tmp_path / "providers" / "laposte" / "products.json"
        doc = json.loads(products_path.read_text(encoding="utf-8"))
        doc["products"].extend(
            [
                {
                    "id": "no_porto",
                    "zones": ["domestic"],
                    "delivery": delivery,
                },
                {
                    "id": "bad_zones",
                    "porto_id": "small",
                    "zones": ["domestic"],
                    "delivery": delivery,
                },
                {
                    "id": "bad_tiers",
                    "porto_id": "small",
                    "zones": ["domestic"],
                    "delivery": delivery,
                },
                {
                    "id": "bad_zone_type",
                    "porto_id": "small",
                    "zones": ["domestic"],
                    "delivery": delivery,
                },
                {
                    "id": "bad_tier_type",
                    "porto_id": "small",
                    "zones": ["domestic"],
                    "delivery": delivery,
                },
            ]
        )
        products_path.write_text(json.dumps(doc), encoding="utf-8")
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            assert validate_products_delivery() == 0

    def test_load_feature_ids_not_list(self, tmp_path) -> None:
        from scripts.validators.products_delivery import _load_feature_ids

        prov_dir = tmp_path / "providers" / "laposte"
        prov_dir.mkdir(parents=True)
        (prov_dir / "features.json").write_text(
            json.dumps({"file_type": "features", "provider": "laposte", "features": "bad"}),
            encoding="utf-8",
        )
        (tmp_path / "mappings.json").write_text(
            json.dumps(
                {
                    "mappings": {
                        "providers": {
                            "laposte": {
                                "schemas/features.schema.json": "providers/laposte/features.json",
                            }
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            assert _load_feature_ids("laposte", tmp_path) == set()

    def test_load_graph_edges_not_dict(self, tmp_path) -> None:
        from scripts.validators.products_delivery import _load_graph_product_edges

        prov_dir = tmp_path / "providers" / "laposte"
        prov_dir.mkdir(parents=True)
        graph_path = prov_dir / "graph.json"
        graph_path.write_text(
            json.dumps({"file_type": "graph", "provider": "laposte", "edges": "bad"}),
            encoding="utf-8",
        )
        (tmp_path / "mappings.json").write_text(
            json.dumps(
                {
                    "mappings": {
                        "providers": {
                            "laposte": {
                                "schemas/graph.schema.json": "providers/laposte/graph.json",
                            }
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            assert _load_graph_product_edges("laposte", tmp_path) == {}

        graph_path.write_text(
            json.dumps({"file_type": "graph", "provider": "laposte", "edges": {"products": "bad"}}),
            encoding="utf-8",
        )
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            assert _load_graph_product_edges("laposte", tmp_path) == {}
