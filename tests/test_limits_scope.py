"""Tests for limits_scope validator."""

import json
from pathlib import Path
from typing import Any

import pytest

from scripts.validators.limits_scope import validate_limits_scope

_ACME_REG = {
    "name": "Acme",
    "country": "XX",
    "timezone": "Etc/UTC",
    "mark_types": ["stamp"],
    "tracking_model": "mixed",
}


def _write_limits_bundle(
    tmp_path: Path,
    *,
    mappings_providers: dict[str, Any],
    limits_body: dict[str, Any] | None,
    write_limits_file: bool = True,
) -> None:
    (tmp_path / "global").mkdir(parents=True)
    prov_ids = list(mappings_providers.keys())
    (tmp_path / "global" / "providers.json").write_text(
        json.dumps({"providers": {pid: _ACME_REG for pid in prov_ids}}),
        encoding="utf-8",
    )
    (tmp_path / "mappings.json").write_text(
        json.dumps({"mappings": {"global": {}, "providers": mappings_providers}}),
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


def test_validate_limits_scope_errors_on_provider_mismatch(tmp_path: Path):
    good = {
        "file_type": "limits",
        "provider": "wrong",
        "limits": [],
        "compliance_frameworks": {},
    }
    _write_limits_bundle(
        tmp_path,
        mappings_providers={
            "acme": {"schemas/limits.schema.json": "providers/acme/limits.json"}
        },
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
            "provider": "acme",
            "limits": [],
            "compliance_frameworks": {},
        },
    )
    assert validate_limits_scope(project_root=tmp_path) == 1


def test_validate_limits_scope_errors_when_mapped_file_missing(tmp_path: Path):
    _write_limits_bundle(
        tmp_path,
        mappings_providers={
            "acme": {"schemas/limits.schema.json": "providers/acme/limits.json"}
        },
        limits_body=None,
        write_limits_file=False,
    )
    assert validate_limits_scope(project_root=tmp_path) == 1


def test_validate_limits_scope_errors_on_invalid_json(tmp_path: Path):
    _write_limits_bundle(
        tmp_path,
        mappings_providers={
            "acme": {"schemas/limits.schema.json": "providers/acme/limits.json"}
        },
        limits_body=None,
        write_limits_file=False,
    )
    (tmp_path / "providers" / "acme" / "limits.json").write_text("{", encoding="utf-8")
    assert validate_limits_scope(project_root=tmp_path) == 1


def test_validate_limits_scope_errors_on_wrong_file_type(tmp_path: Path):
    _write_limits_bundle(
        tmp_path,
        mappings_providers={
            "acme": {"schemas/limits.schema.json": "providers/acme/limits.json"}
        },
        limits_body={
            "file_type": "other",
            "provider": "acme",
            "limits": [],
            "compliance_frameworks": {},
        },
    )
    assert validate_limits_scope(project_root=tmp_path) == 1


def test_validate_limits_scope_errors_when_limits_not_array(tmp_path: Path):
    _write_limits_bundle(
        tmp_path,
        mappings_providers={
            "acme": {"schemas/limits.schema.json": "providers/acme/limits.json"}
        },
        limits_body={
            "file_type": "limits",
            "provider": "acme",
            "limits": {},
            "compliance_frameworks": {},
        },
    )
    assert validate_limits_scope(project_root=tmp_path) == 1


def test_validate_limits_scope_errors_when_compliance_frameworks_null(tmp_path: Path):
    _write_limits_bundle(
        tmp_path,
        mappings_providers={
            "acme": {"schemas/limits.schema.json": "providers/acme/limits.json"}
        },
        limits_body={
            "file_type": "limits",
            "provider": "acme",
            "limits": [],
            "compliance_frameworks": None,
        },
    )
    assert validate_limits_scope(project_root=tmp_path) == 1


def test_validate_limits_scope_errors_when_compliance_frameworks_not_object(
    tmp_path: Path,
):
    _write_limits_bundle(
        tmp_path,
        mappings_providers={
            "acme": {"schemas/limits.schema.json": "providers/acme/limits.json"}
        },
        limits_body={
            "file_type": "limits",
            "provider": "acme",
            "limits": [],
            "compliance_frameworks": [],
        },
    )
    assert validate_limits_scope(project_root=tmp_path) == 1


def test_validate_limits_scope_errors_on_non_object_limit_row(tmp_path: Path):
    _write_limits_bundle(
        tmp_path,
        mappings_providers={
            "acme": {"schemas/limits.schema.json": "providers/acme/limits.json"}
        },
        limits_body={
            "file_type": "limits",
            "provider": "acme",
            "limits": ["bad"],
            "compliance_frameworks": {},
        },
    )
    assert validate_limits_scope(project_root=tmp_path) == 1


def test_validate_limits_scope_errors_on_missing_row_id(tmp_path: Path):
    _write_limits_bundle(
        tmp_path,
        mappings_providers={
            "acme": {"schemas/limits.schema.json": "providers/acme/limits.json"}
        },
        limits_body={
            "file_type": "limits",
            "provider": "acme",
            "limits": [{}],
            "compliance_frameworks": {},
        },
    )
    assert validate_limits_scope(project_root=tmp_path) == 1


def test_validate_limits_scope_errors_on_duplicate_row_ids(tmp_path: Path):
    _write_limits_bundle(
        tmp_path,
        mappings_providers={
            "acme": {"schemas/limits.schema.json": "providers/acme/limits.json"}
        },
        limits_body={
            "file_type": "limits",
            "provider": "acme",
            "limits": [
                {"id": "x", "framework_id": None},
                {"id": "x", "framework_id": None},
            ],
            "compliance_frameworks": {},
        },
    )
    assert validate_limits_scope(project_root=tmp_path) == 1


def test_validate_limits_scope_errors_on_unknown_framework_id(tmp_path: Path):
    _write_limits_bundle(
        tmp_path,
        mappings_providers={
            "acme": {"schemas/limits.schema.json": "providers/acme/limits.json"}
        },
        limits_body={
            "file_type": "limits",
            "provider": "acme",
            "limits": [{"id": "r1", "framework_id": "nope"}],
            "compliance_frameworks": {},
        },
    )
    assert validate_limits_scope(project_root=tmp_path) == 1


def test_validate_limits_scope_errors_when_framework_entry_not_object(tmp_path: Path):
    _write_limits_bundle(
        tmp_path,
        mappings_providers={
            "acme": {"schemas/limits.schema.json": "providers/acme/limits.json"}
        },
        limits_body={
            "file_type": "limits",
            "provider": "acme",
            "limits": [],
            "compliance_frameworks": {"fw1": "x"},
        },
    )
    assert validate_limits_scope(project_root=tmp_path) == 1


def test_validate_limits_scope_errors_on_framework_timezone_mismatch(tmp_path: Path):
    _write_limits_bundle(
        tmp_path,
        mappings_providers={
            "acme": {"schemas/limits.schema.json": "providers/acme/limits.json"}
        },
        limits_body={
            "file_type": "limits",
            "provider": "acme",
            "limits": [],
            "compliance_frameworks": {
                "fw1": {"timezone": "Europe/Berlin"},
            },
        },
    )
    assert validate_limits_scope(project_root=tmp_path) == 1


def test_validate_limits_scope_warns_on_unreferenced_framework(tmp_path: Path, capsys):
    _write_limits_bundle(
        tmp_path,
        mappings_providers={
            "acme": {"schemas/limits.schema.json": "providers/acme/limits.json"}
        },
        limits_body={
            "file_type": "limits",
            "provider": "acme",
            "limits": [{"id": "r1", "framework_id": "fw1"}],
            "compliance_frameworks": {
                "fw1": {"timezone": "Etc/UTC"},
                "fw2": {"timezone": "Etc/UTC"},
            },
        },
    )
    assert validate_limits_scope(project_root=tmp_path) == 0
    err = capsys.readouterr().out
    assert "WARNING" in err
    assert "fw2" in err


def test_validate_limits_scope_passes_when_registry_providers_not_dict(tmp_path: Path):
    (tmp_path / "global").mkdir()
    (tmp_path / "global" / "providers.json").write_text(
        json.dumps({"providers": "broken"}),
        encoding="utf-8",
    )
    (tmp_path / "mappings.json").write_text(
        json.dumps(
            {
                "mappings": {
                    "global": {},
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
                "provider": "acme",
                "limits": [],
                "compliance_frameworks": {},
            }
        ),
        encoding="utf-8",
    )
    assert validate_limits_scope(project_root=tmp_path) == 0
