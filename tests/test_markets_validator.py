"""Branch coverage for scripts/validators/markets.py and load_markets()."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

import scripts.data_files as data_files
from scripts.validators.markets import validate_markets


def _write_registry(tmp_path, *, countries: dict[str, str]) -> None:
    providers = {
        pid: {"label": pid, "name": f"{pid} entity", "country": cc, "mark_types": ["stamp"]}
        for pid, cc in countries.items()
    }
    (tmp_path / "providers.json").write_text(
        json.dumps({"providers": providers}),
        encoding="utf-8",
    )


def _write_markets(tmp_path, markets: dict) -> None:
    (tmp_path / "policy").mkdir(exist_ok=True)
    (tmp_path / "policy" / "markets.json").write_text(
        json.dumps({"file_type": "markets", "unit": {}, "markets": markets}),
        encoding="utf-8",
    )


class TestLoadMarketsErrors:
    def test_raises_when_markets_missing(self, tmp_path):
        (tmp_path / "mappings.json").write_text(
            json.dumps(
                {"mappings": {"policy": {}, "formats": {}, "registry": {}, "providers": {}}}
            ),
            encoding="utf-8",
        )
        with (
            patch.object(data_files, "_get_project_root", return_value=tmp_path),
            pytest.raises(FileNotFoundError, match="Markets policy not found"),
        ):
            data_files.load_markets()

    def test_load_markets_via_mappings_path(self, tmp_path):
        (tmp_path / "policy").mkdir()
        alt = tmp_path / "policy" / "markets-alt.json"
        alt.write_text(
            json.dumps(
                {
                    "file_type": "markets",
                    "markets": {"DE": {"currency": "EUR"}},
                }
            ),
            encoding="utf-8",
        )
        (tmp_path / "mappings.json").write_text(
            json.dumps(
                {
                    "mappings": {
                        "policy": {
                            "schemas/markets.schema.json": "policy/markets-alt.json",
                        },
                        "formats": {},
                        "registry": {},
                        "providers": {},
                    }
                }
            ),
            encoding="utf-8",
        )
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            doc = data_files.load_markets()
        assert doc["markets"]["DE"]["currency"] == "EUR"

    def test_raises_when_markets_empty(self, tmp_path):
        (tmp_path / "policy").mkdir()
        (tmp_path / "policy" / "markets.json").write_text(
            json.dumps({"file_type": "markets", "markets": {}}),
            encoding="utf-8",
        )
        with (
            patch.object(data_files, "_get_project_root", return_value=tmp_path),
            pytest.raises(ValueError, match="non-empty object 'markets'"),
        ):
            data_files.load_markets()

    def test_market_for_country_bad_doc(self):
        with pytest.raises(ValueError, match="missing 'markets'"):
            data_files.market_for_country("DE", markets_doc={"file_type": "markets"})


class TestValidateMarketsBranches:
    def test_missing_market_for_provider_country(self, tmp_path, capsys):
        _write_registry(tmp_path, countries={"deutschepost": "DE"})
        _write_markets(tmp_path, {"FR": {"currency": "EUR"}})
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            assert validate_markets() == 1
        out = capsys.readouterr().out
        assert "markets.DE" in out or "DE" in out

    def test_market_row_not_dict(self, tmp_path, capsys):
        _write_registry(tmp_path, countries={"deutschepost": "DE"})
        _write_markets(tmp_path, {"DE": "not-a-dict"})
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            assert validate_markets() == 1
        assert "markets.DE: entry must be an object" in capsys.readouterr().out

    def test_invalid_currency_and_intl_overlap(self, tmp_path, capsys):
        _write_registry(tmp_path, countries={"deutschepost": "DE"})
        _write_markets(
            tmp_path,
            {
                "DE": {
                    "currency": "BAD",
                    "international_currency": ["EUR"],
                    "vat": {"exempt": True, "rate": 0.2},
                    "settlement": "not-a-dict",
                }
            },
        )
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            assert validate_markets() == 1
        out = capsys.readouterr().out
        assert "currency must be one of" in out
        assert "vat.rate must be omitted" in out
        assert "settlement must be an object" in out

    def test_international_currency_validation(self, tmp_path, capsys):
        _write_registry(tmp_path, countries={"deutschepost": "DE"})
        _write_markets(
            tmp_path,
            {
                "DE": {
                    "currency": "EUR",
                    "international_currency": ["EUR"],
                }
            },
        )
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            assert validate_markets() == 1
        assert "must not include domestic currency" in capsys.readouterr().out

    def test_load_markets_file_error(self, tmp_path, capsys, monkeypatch):
        def _boom() -> dict:
            raise FileNotFoundError("missing markets file")

        monkeypatch.setattr("scripts.validators.markets.load_markets", _boom)
        assert validate_markets() == 1
        assert "missing markets file" in capsys.readouterr().out

    def test_load_markets_value_error(self, capsys, monkeypatch):
        def _bad() -> dict:
            raise ValueError("bad markets doc")

        monkeypatch.setattr("scripts.validators.markets.load_markets", _bad)
        assert validate_markets() == 1
        assert "bad markets doc" in capsys.readouterr().out

    def test_load_markets_value_error_on_bad_structure(self, tmp_path, capsys, monkeypatch):
        monkeypatch.setattr(
            "scripts.validators.markets.load_markets",
            lambda: {"file_type": "markets", "markets": []},
        )
        assert validate_markets() == 1
        assert "missing 'markets' object" in capsys.readouterr().out

    def test_deprecated_market_keys(self, tmp_path, capsys):
        _write_registry(tmp_path, countries={"deutschepost": "DE"})
        _write_markets(
            tmp_path,
            {
                "DE": {
                    "currency": "EUR",
                    "intl_ccy": ["USD"],
                    "vat": {"inclusive": True, "intl_excl": True},
                }
            },
        )
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            assert validate_markets() == 1
        out = capsys.readouterr().out
        assert "deprecated key 'intl_ccy'" in out
        assert "deprecated vat.inclusive" in out
        assert "deprecated vat.intl_excl" in out

    def test_vat_exempt_with_domestic_lane(self, tmp_path, capsys):
        _write_registry(tmp_path, countries={"deutschepost": "DE"})
        _write_markets(
            tmp_path,
            {
                "DE": {
                    "currency": "EUR",
                    "vat": {"exempt": True, "domestic": {"inclusive": True}},
                }
            },
        )
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            assert validate_markets() == 1
        assert "vat.domestic/international must be omitted" in capsys.readouterr().out

    def test_vat_not_dict(self, tmp_path, capsys):
        _write_registry(tmp_path, countries={"deutschepost": "DE"})
        _write_markets(tmp_path, {"DE": {"currency": "EUR", "vat": "bad"}})
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            assert validate_markets() == 1
        assert "vat must be an object" in capsys.readouterr().out

    def test_empty_international_currency_array(self, tmp_path, capsys):
        _write_registry(tmp_path, countries={"deutschepost": "DE"})
        _write_markets(tmp_path, {"DE": {"currency": "EUR", "international_currency": []}})
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            assert validate_markets() == 1
        assert "international_currency must be a non-empty array" in capsys.readouterr().out

    def test_invalid_international_currency_entry(self, tmp_path, capsys):
        _write_registry(tmp_path, countries={"deutschepost": "DE"})
        _write_markets(tmp_path, {"DE": {"currency": "EUR", "international_currency": ["BAD"]}})
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            assert validate_markets() == 1
        assert "international_currency entry" in capsys.readouterr().out

    def test_provider_countries_not_dict(self, tmp_path, capsys, monkeypatch):
        monkeypatch.setattr(
            "scripts.validators.markets.load_providers_registry",
            lambda: {"providers": "bad"},
        )
        monkeypatch.setattr(
            "scripts.validators.markets.load_markets",
            lambda: {"markets": {"DE": {"currency": "EUR"}}},
        )
        assert validate_markets() == 0

    def test_missing_market_for_extra_registry_provider(self, tmp_path, capsys):
        _write_registry(
            tmp_path,
            countries={
                "deutschepost": "DE",
                "newoperator": "PL",
            },
        )
        _write_markets(tmp_path, {"DE": {"currency": "EUR"}})
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            assert validate_markets() == 1
        out = capsys.readouterr().out
        assert "providers.newoperator.country 'PL'" in out

    def test_provider_row_skips_non_dict_country(self, tmp_path, capsys, monkeypatch):
        monkeypatch.setattr(
            "scripts.validators.markets.load_providers_registry",
            lambda: {
                "providers": {
                    "deutschepost": {
                        "label": "DP",
                        "name": "DP AG",
                        "country": "DE",
                        "mark_types": ["stamp"],
                    },
                    "ghost": "bad",
                }
            },
        )
        monkeypatch.setattr(
            "scripts.validators.markets.load_markets",
            lambda: {"markets": {"DE": {"currency": "EUR"}}},
        )
        assert validate_markets() == 0
