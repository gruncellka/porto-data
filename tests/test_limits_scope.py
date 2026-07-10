"""Tests for limits_scope validator."""

import json
from pathlib import Path
from typing import Any

import pytest

from scripts.validators import limits_scope as limits_scope_mod
from scripts.validators.limits_scope import (
    _jurisdiction_country_timezones,
    _list_provider_ids,
    _provider_timezones,
    validate_limits_scope,
)

_ACME_REG = {
    "label": "Acme",
    "name": "Acme Ltd",
    "country": "XX",
    "mark_types": ["stamp"],
    "tracking_model": "mixed",
}

_MIN_JURISDICTIONS = {
    "file_type": "jurisdictions",
    "unit": {"country_code": "ISO 3166-1 alpha-2"},
    "jurisdictions": {
        "eu": {"members": ["AT"], "timezone": "Europe/Brussels"},
        "un": {"members": ["AD"], "timezone": "Europe/Zurich"},
        "CH": {"timezone": "Europe/Zurich"},
        "XX": {"timezone": "Etc/UTC"},
    },
}


def _write_limits_bundle(
    tmp_path: Path,
    *,
    mappings_providers: dict[str, Any],
    limits_body: dict[str, Any] | None,
    write_limits_file: bool = True,
) -> None:
    (tmp_path / "policy").mkdir(parents=True)
    prov_ids = list(mappings_providers.keys())
    (tmp_path / "providers.json").write_text(
        json.dumps({"providers": dict.fromkeys(prov_ids, _ACME_REG)}),
        encoding="utf-8",
    )
    (tmp_path / "policy" / "jurisdictions.json").write_text(
        json.dumps(_MIN_JURISDICTIONS),
        encoding="utf-8",
    )
    (tmp_path / "mappings.json").write_text(
        json.dumps(
            {
                "mappings": {
                    "policy": {},
                    "formats": {},
                    "registry": {},
                    "providers": mappings_providers,
                }
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "providers" / "acme").mkdir(parents=True)
    if len(prov_ids) > 1:
        for pid in prov_ids[1:]:
            (tmp_path / "providers" / pid).mkdir(parents=True)
    if write_limits_file and limits_body is not None:
        (tmp_path / "providers" / "acme" / "limits.json").write_text(
            json.dumps(limits_body), encoding="utf-8"
        )


def test_validate_limits_scope_passes_on_real_porto_data():
    root = Path(__file__).resolve().parent.parent / "porto_data"
    assert root.is_dir()
    assert validate_limits_scope(project_root=root) == 0


def test_validate_limits_scope_errors_on_redundant_provider_field(tmp_path: Path):
    good = {
        "file_type": "limits",
        "provider": "wrong",
        "limits": [],
        "frameworks": {},
    }
    _write_limits_bundle(
        tmp_path,
        mappings_providers={"acme": {"schemas/limits.schema.json": "providers/acme/limits.json"}},
        limits_body=good,
    )
    assert validate_limits_scope(project_root=tmp_path) == 1


def test_validate_limits_scope_errors_when_limits_mapping_missing_for_second_provider(
    tmp_path: Path,
):
    _write_limits_bundle(
        tmp_path,
        mappings_providers={
            "acme": {"schemas/limits.schema.json": "providers/acme/limits.json"},
            "beta": {},
        },
        limits_body={
            "file_type": "limits",
            "limits": [],
            "frameworks": {},
        },
    )
    assert validate_limits_scope(project_root=tmp_path) == 1


def test_validate_limits_scope_errors_when_mapped_file_missing(tmp_path: Path):
    _write_limits_bundle(
        tmp_path,
        mappings_providers={"acme": {"schemas/limits.schema.json": "providers/acme/limits.json"}},
        limits_body=None,
        write_limits_file=False,
    )
    assert validate_limits_scope(project_root=tmp_path) == 1


def test_validate_limits_scope_errors_on_invalid_json(tmp_path: Path):
    _write_limits_bundle(
        tmp_path,
        mappings_providers={"acme": {"schemas/limits.schema.json": "providers/acme/limits.json"}},
        limits_body=None,
        write_limits_file=False,
    )
    (tmp_path / "providers" / "acme" / "limits.json").write_text("{", encoding="utf-8")
    assert validate_limits_scope(project_root=tmp_path) == 1


def test_validate_limits_scope_errors_on_wrong_file_type(tmp_path: Path):
    _write_limits_bundle(
        tmp_path,
        mappings_providers={"acme": {"schemas/limits.schema.json": "providers/acme/limits.json"}},
        limits_body={
            "file_type": "other",
            "limits": [],
            "frameworks": {},
        },
    )
    assert validate_limits_scope(project_root=tmp_path) == 1


def test_validate_limits_scope_errors_when_limits_not_array(tmp_path: Path):
    _write_limits_bundle(
        tmp_path,
        mappings_providers={"acme": {"schemas/limits.schema.json": "providers/acme/limits.json"}},
        limits_body={
            "file_type": "limits",
            "limits": {},
            "frameworks": {},
        },
    )
    assert validate_limits_scope(project_root=tmp_path) == 1


def test_validate_limits_scope_errors_when_frameworks_null(tmp_path: Path):
    _write_limits_bundle(
        tmp_path,
        mappings_providers={"acme": {"schemas/limits.schema.json": "providers/acme/limits.json"}},
        limits_body={
            "file_type": "limits",
            "limits": [],
            "frameworks": None,
        },
    )
    assert validate_limits_scope(project_root=tmp_path) == 1


def test_validate_limits_scope_errors_when_frameworks_not_object(
    tmp_path: Path,
):
    _write_limits_bundle(
        tmp_path,
        mappings_providers={"acme": {"schemas/limits.schema.json": "providers/acme/limits.json"}},
        limits_body={
            "file_type": "limits",
            "limits": [],
            "frameworks": [],
        },
    )
    assert validate_limits_scope(project_root=tmp_path) == 1


def test_validate_limits_scope_errors_on_non_object_limit_row(tmp_path: Path):
    _write_limits_bundle(
        tmp_path,
        mappings_providers={"acme": {"schemas/limits.schema.json": "providers/acme/limits.json"}},
        limits_body={
            "file_type": "limits",
            "limits": ["bad"],
            "frameworks": {},
        },
    )
    assert validate_limits_scope(project_root=tmp_path) == 1


def test_validate_limits_scope_errors_on_missing_row_id(tmp_path: Path):
    _write_limits_bundle(
        tmp_path,
        mappings_providers={"acme": {"schemas/limits.schema.json": "providers/acme/limits.json"}},
        limits_body={
            "file_type": "limits",
            "limits": [{}],
            "frameworks": {},
        },
    )
    assert validate_limits_scope(project_root=tmp_path) == 1


def test_validate_limits_scope_errors_on_duplicate_row_ids(tmp_path: Path):
    row = {
        "id": "x",
        "country_code": "XX",
        "status": "operational",
        "reason": "r",
        "notes": "n",
        "effective_from": None,
    }
    _write_limits_bundle(
        tmp_path,
        mappings_providers={"acme": {"schemas/limits.schema.json": "providers/acme/limits.json"}},
        limits_body={
            "file_type": "limits",
            "limits": [row, dict(row)],
            "frameworks": {},
        },
    )
    assert validate_limits_scope(project_root=tmp_path) == 1


def test_validate_limits_scope_errors_when_framework_entry_not_object(tmp_path: Path):
    _write_limits_bundle(
        tmp_path,
        mappings_providers={"acme": {"schemas/limits.schema.json": "providers/acme/limits.json"}},
        limits_body={
            "file_type": "limits",
            "limits": [],
            "frameworks": {"fw1": "x"},
        },
    )
    assert validate_limits_scope(project_root=tmp_path) == 1


def test_validate_limits_scope_errors_on_framework_timezone_mismatch(tmp_path: Path):
    _write_limits_bundle(
        tmp_path,
        mappings_providers={"acme": {"schemas/limits.schema.json": "providers/acme/limits.json"}},
        limits_body={
            "file_type": "limits",
            "limits": [],
            "frameworks": {
                "fw1": {"timezone": "Europe/Berlin"},
            },
        },
    )
    assert validate_limits_scope(project_root=tmp_path) == 1


def test_validate_limits_scope_passes_when_registry_providers_not_dict(tmp_path: Path):
    (tmp_path / "policy").mkdir()
    (tmp_path / "providers.json").write_text(
        json.dumps({"providers": "broken"}),
        encoding="utf-8",
    )
    (tmp_path / "mappings.json").write_text(
        json.dumps(
            {
                "mappings": {
                    "policy": {},
                    "formats": {},
                    "registry": {},
                    "providers": {
                        "acme": {
                            "schemas/limits.schema.json": "providers/acme/limits.json",
                        }
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "providers" / "acme").mkdir(parents=True)
    (tmp_path / "providers" / "acme" / "limits.json").write_text(
        json.dumps(
            {
                "file_type": "limits",
                "limits": [],
                "frameworks": {},
            }
        ),
        encoding="utf-8",
    )
    assert validate_limits_scope(project_root=tmp_path) == 0


class TestLimitsScopeHelpers:
    """Cover edge cases in ``_jurisdiction_country_timezones`` / ``_provider_timezones``."""

    def test_list_provider_ids_empty_when_providers_not_dict(self, tmp_path: Path) -> None:
        (tmp_path / "providers.json").write_text(
            json.dumps({"providers": "not-a-dict"}),
            encoding="utf-8",
        )
        assert _list_provider_ids(tmp_path) == []

    def test_jurisdiction_country_timezones_invalid_json(self, tmp_path: Path) -> None:
        (tmp_path / "policy").mkdir()
        (tmp_path / "policy" / "jurisdictions.json").write_text("{not-json", encoding="utf-8")
        assert _jurisdiction_country_timezones(tmp_path) == {}

    def test_jurisdiction_country_timezones_jurisdictions_not_dict(
        self,
        tmp_path: Path,
    ) -> None:
        (tmp_path / "policy").mkdir()
        (tmp_path / "policy" / "jurisdictions.json").write_text(
            json.dumps({"file_type": "jurisdictions", "jurisdictions": []}),
            encoding="utf-8",
        )
        assert _jurisdiction_country_timezones(tmp_path) == {}

    def test_jurisdiction_country_timezones_skips_non_dict_country_blocs(
        self,
        tmp_path: Path,
    ) -> None:
        (tmp_path / "policy").mkdir()
        (tmp_path / "policy" / "jurisdictions.json").write_text(
            json.dumps(
                {
                    "file_type": "jurisdictions",
                    "jurisdictions": {
                        "DE": "broken",
                        "FR": {"timezone": "Europe/Paris"},
                    },
                }
            ),
            encoding="utf-8",
        )
        assert _jurisdiction_country_timezones(tmp_path) == {"FR": "Europe/Paris"}

    def test_jurisdiction_country_timezones_skips_bad_country_codes(
        self,
        tmp_path: Path,
    ) -> None:
        (tmp_path / "policy").mkdir()
        (tmp_path / "policy" / "jurisdictions.json").write_text(
            json.dumps(
                {
                    "file_type": "jurisdictions",
                    "jurisdictions": {
                        "de": {"timezone": "Europe/Berlin"},
                        "D": {"timezone": "Europe/Berlin"},
                        "AT": {"timezone": "Europe/Vienna"},
                    },
                }
            ),
            encoding="utf-8",
        )
        assert _jurisdiction_country_timezones(tmp_path) == {"AT": "Europe/Vienna"}

    def test_jurisdiction_country_timezones_empty_when_resolved_path_missing(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        ghost = tmp_path / "missing-jurisdictions.json"

        def _fake_get_data_file_path(entity: str, **_kwargs: Any) -> Path:
            assert entity == "jurisdictions"
            return ghost

        monkeypatch.setattr(limits_scope_mod, "get_data_file_path", _fake_get_data_file_path)
        assert _jurisdiction_country_timezones(tmp_path) == {}

    def test_provider_timezones_skips_non_dict_registry_rows(self, tmp_path: Path) -> None:
        (tmp_path / "policy").mkdir()
        (tmp_path / "policy" / "jurisdictions.json").write_text(
            json.dumps(
                {
                    "file_type": "jurisdictions",
                    "jurisdictions": {"DE": {"timezone": "Europe/Berlin"}},
                }
            ),
            encoding="utf-8",
        )
        (tmp_path / "providers.json").write_text(
            json.dumps(
                {
                    "providers": {
                        "good": {"country": "DE"},
                        "bad": "not-a-dict",
                    }
                }
            ),
            encoding="utf-8",
        )
        assert _provider_timezones(tmp_path) == {"good": "Europe/Berlin"}

    def test_provider_timezones_skips_short_or_blank_country(self, tmp_path: Path) -> None:
        (tmp_path / "policy").mkdir()
        (tmp_path / "policy" / "jurisdictions.json").write_text(
            json.dumps(
                {
                    "file_type": "jurisdictions",
                    "jurisdictions": {"DE": {"timezone": "Europe/Berlin"}},
                }
            ),
            encoding="utf-8",
        )
        (tmp_path / "providers.json").write_text(
            json.dumps(
                {
                    "providers": {
                        "ok": {"country": "DE"},
                        "short": {"country": "D"},
                        "blank": {"country": "   "},
                        "not_str": {"country": 99},
                    }
                }
            ),
            encoding="utf-8",
        )
        assert _provider_timezones(tmp_path) == {"ok": "Europe/Berlin"}
