"""Tests for mappings_layout validator."""

import json
from pathlib import Path

import pytest

from scripts.validators.mappings_layout import validate_mappings_layout


def _patch_bundle_root(monkeypatch: pytest.MonkeyPatch, root: Path) -> None:
    """Make all data_files resolution use ``root`` (mappings.json + policy/formats + providers/)."""
    monkeypatch.setattr("scripts.data_files._get_project_root", lambda: root)


def _acme_row() -> dict:
    return {
        "name": "Acme",
        "country": "XX",
        "mark_types": ["stamp"],
        "tracking_model": "mixed",
    }


def test_validate_mappings_layout_passes_on_real_porto_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = Path(__file__).resolve().parent.parent / "porto_data"
    assert root.is_dir()
    _patch_bundle_root(monkeypatch, root)
    assert validate_mappings_layout() == 0


def test_validate_mappings_layout_errors_on_provider_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_bundle_root(monkeypatch, tmp_path)
    (tmp_path / "policy").mkdir()
    (tmp_path / "providers.json").write_text(
        json.dumps({"providers": {"acme": _acme_row()}}),
        encoding="utf-8",
    )
    mappings = {
        "mappings": {
            "policy": {},
            "formats": {},
            "registry": {},
            "providers": {
                "acme": {
                    "schemas/products.schema.json": "providers/acme/products.json",
                }
            },
        }
    }
    (tmp_path / "mappings.json").write_text(json.dumps(mappings), encoding="utf-8")
    (tmp_path / "providers" / "acme").mkdir(parents=True)
    (tmp_path / "providers" / "acme" / "products.json").write_text(
        json.dumps({"provider": "wrong", "products": []}),
        encoding="utf-8",
    )

    assert validate_mappings_layout() == 1


def test_validate_mappings_layout_errors_on_stray_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_bundle_root(monkeypatch, tmp_path)
    (tmp_path / "policy").mkdir()
    (tmp_path / "providers.json").write_text(
        json.dumps({"providers": {"acme": _acme_row()}}),
        encoding="utf-8",
    )
    mappings = {
        "mappings": {
            "policy": {},
            "formats": {},
            "registry": {},
            "providers": {
                "acme": {
                    "schemas/products.schema.json": "providers/acme/products.json",
                }
            },
        }
    }
    (tmp_path / "mappings.json").write_text(json.dumps(mappings), encoding="utf-8")
    (tmp_path / "providers" / "acme").mkdir(parents=True)
    (tmp_path / "providers" / "acme" / "products.json").write_text(
        json.dumps({"provider": "acme", "products": []}),
        encoding="utf-8",
    )
    (tmp_path / "providers" / "acme" / "orphan.json").write_text(
        json.dumps({"provider": "acme"}),
        encoding="utf-8",
    )

    assert validate_mappings_layout() == 1


def test_validate_mappings_layout_errors_when_registry_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_bundle_root(monkeypatch, tmp_path)
    (tmp_path / "mappings.json").write_text(
        json.dumps({"mappings": {"policy": {}, "formats": {}, "registry": {}, "providers": {}}}),
        encoding="utf-8",
    )
    assert validate_mappings_layout() == 1


def test_validate_mappings_layout_errors_on_invalid_registry_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_bundle_root(monkeypatch, tmp_path)
    (tmp_path / "policy").mkdir()
    (tmp_path / "providers.json").write_text("{", encoding="utf-8")
    (tmp_path / "mappings.json").write_text(
        json.dumps({"mappings": {"policy": {}, "formats": {}, "registry": {}, "providers": {}}}),
        encoding="utf-8",
    )
    assert validate_mappings_layout() == 1


def test_validate_mappings_layout_errors_on_empty_registry_providers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_bundle_root(monkeypatch, tmp_path)
    (tmp_path / "policy").mkdir()
    (tmp_path / "providers.json").write_text(json.dumps({"providers": {}}), encoding="utf-8")
    (tmp_path / "mappings.json").write_text(
        json.dumps({"mappings": {"policy": {}, "formats": {}, "registry": {}, "providers": {}}}),
        encoding="utf-8",
    )
    assert validate_mappings_layout() == 1


def test_validate_mappings_layout_errors_registry_keys_differ_from_mappings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_bundle_root(monkeypatch, tmp_path)
    (tmp_path / "policy").mkdir()
    (tmp_path / "providers.json").write_text(
        json.dumps({"providers": {"acme": _acme_row()}}),
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
                        "other": {
                            "schemas/products.schema.json": "providers/other/products.json",
                        }
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    assert validate_mappings_layout() == 1


def test_validate_mappings_layout_errors_when_providers_block_not_object(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_bundle_root(monkeypatch, tmp_path)
    (tmp_path / "policy").mkdir()
    (tmp_path / "providers.json").write_text(
        json.dumps({"providers": {"acme": _acme_row()}}),
        encoding="utf-8",
    )
    (tmp_path / "mappings.json").write_text(
        json.dumps({"mappings": {"policy": {}, "formats": {}, "registry": {}, "providers": []}}),
        encoding="utf-8",
    )
    assert validate_mappings_layout() == 1


def test_validate_mappings_layout_errors_when_provider_dir_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_bundle_root(monkeypatch, tmp_path)
    (tmp_path / "policy").mkdir()
    (tmp_path / "providers.json").write_text(
        json.dumps({"providers": {"acme": _acme_row()}}),
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
                            "schemas/products.schema.json": "providers/acme/products.json",
                        }
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    assert validate_mappings_layout() == 1


def test_validate_mappings_layout_errors_when_provider_mappings_not_object(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_bundle_root(monkeypatch, tmp_path)
    (tmp_path / "policy").mkdir()
    (tmp_path / "providers.json").write_text(
        json.dumps({"providers": {"acme": _acme_row()}}),
        encoding="utf-8",
    )
    (tmp_path / "mappings.json").write_text(
        json.dumps(
            {"mappings": {"policy": {}, "formats": {}, "registry": {}, "providers": {"acme": "bad"}}}
        ),
        encoding="utf-8",
    )
    assert validate_mappings_layout() == 1


def test_validate_mappings_layout_errors_on_non_string_data_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_bundle_root(monkeypatch, tmp_path)
    (tmp_path / "policy").mkdir()
    (tmp_path / "providers.json").write_text(
        json.dumps({"providers": {"acme": _acme_row()}}),
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
                        "acme": {"schemas/products.schema.json": 123},
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "providers" / "acme").mkdir(parents=True)
    assert validate_mappings_layout() == 1


def test_validate_mappings_layout_errors_when_mapped_file_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_bundle_root(monkeypatch, tmp_path)
    (tmp_path / "policy").mkdir()
    (tmp_path / "providers.json").write_text(
        json.dumps({"providers": {"acme": _acme_row()}}),
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
                            "schemas/products.schema.json": "providers/acme/products.json",
                        }
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "providers" / "acme").mkdir(parents=True)
    assert validate_mappings_layout() == 1


def test_validate_mappings_layout_errors_on_invalid_mapped_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_bundle_root(monkeypatch, tmp_path)
    (tmp_path / "policy").mkdir()
    (tmp_path / "providers.json").write_text(
        json.dumps({"providers": {"acme": _acme_row()}}),
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
                            "schemas/products.schema.json": "providers/acme/products.json",
                        }
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "providers" / "acme").mkdir(parents=True)
    (tmp_path / "providers" / "acme" / "products.json").write_text("{", encoding="utf-8")
    assert validate_mappings_layout() == 1


def test_validate_mappings_layout_errors_when_mapped_root_not_object(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_bundle_root(monkeypatch, tmp_path)
    (tmp_path / "policy").mkdir()
    (tmp_path / "providers.json").write_text(
        json.dumps({"providers": {"acme": _acme_row()}}),
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
                            "schemas/products.schema.json": "providers/acme/products.json",
                        }
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "providers" / "acme").mkdir(parents=True)
    (tmp_path / "providers" / "acme" / "products.json").write_text("[]", encoding="utf-8")
    assert validate_mappings_layout() == 1


def test_validate_mappings_layout_errors_when_doc_missing_provider_field(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_bundle_root(monkeypatch, tmp_path)
    (tmp_path / "policy").mkdir()
    (tmp_path / "providers.json").write_text(
        json.dumps({"providers": {"acme": _acme_row()}}),
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
                            "schemas/products.schema.json": "providers/acme/products.json",
                        }
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "providers" / "acme").mkdir(parents=True)
    (tmp_path / "providers" / "acme" / "products.json").write_text(
        json.dumps({"products": []}),
        encoding="utf-8",
    )
    assert validate_mappings_layout() == 1


def test_validate_mappings_layout_errors_on_orphan_provider_folder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_bundle_root(monkeypatch, tmp_path)
    (tmp_path / "policy").mkdir()
    (tmp_path / "providers.json").write_text(
        json.dumps({"providers": {"acme": _acme_row()}}),
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
                            "schemas/products.schema.json": "providers/acme/products.json",
                        }
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "providers" / "acme").mkdir(parents=True)
    (tmp_path / "providers" / "acme" / "products.json").write_text(
        json.dumps({"provider": "acme", "products": []}),
        encoding="utf-8",
    )
    (tmp_path / "providers" / "stray").mkdir()
    assert validate_mappings_layout() == 1


def test_validate_mappings_layout_errors_on_bad_metadata_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_bundle_root(monkeypatch, tmp_path)
    (tmp_path / "policy").mkdir()
    (tmp_path / "providers.json").write_text(
        json.dumps({"providers": {"acme": _acme_row()}}),
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
                            "schemas/products.schema.json": "providers/acme/products.json",
                        }
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "providers" / "acme").mkdir(parents=True)
    (tmp_path / "providers" / "acme" / "products.json").write_text(
        json.dumps({"provider": "acme", "products": []}),
        encoding="utf-8",
    )
    (tmp_path / "metadata.json").write_text("{", encoding="utf-8")
    assert validate_mappings_layout() == 1


def test_validate_mappings_layout_errors_when_metadata_providers_not_object(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_bundle_root(monkeypatch, tmp_path)
    (tmp_path / "policy").mkdir()
    (tmp_path / "providers.json").write_text(
        json.dumps({"providers": {"acme": _acme_row()}}),
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
                            "schemas/products.schema.json": "providers/acme/products.json",
                        }
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "providers" / "acme").mkdir(parents=True)
    (tmp_path / "providers" / "acme" / "products.json").write_text(
        json.dumps({"provider": "acme", "products": []}),
        encoding="utf-8",
    )
    (tmp_path / "metadata.json").write_text(
        json.dumps({"providers": []}),
        encoding="utf-8",
    )
    assert validate_mappings_layout() == 1


def test_validate_mappings_layout_errors_on_metadata_provider_key_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_bundle_root(monkeypatch, tmp_path)
    (tmp_path / "policy").mkdir()
    (tmp_path / "providers.json").write_text(
        json.dumps({"providers": {"acme": _acme_row()}}),
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
                            "schemas/products.schema.json": "providers/acme/products.json",
                        }
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "providers" / "acme").mkdir(parents=True)
    (tmp_path / "providers" / "acme" / "products.json").write_text(
        json.dumps({"provider": "acme", "products": []}),
        encoding="utf-8",
    )
    (tmp_path / "metadata.json").write_text(
        json.dumps({"providers": {"beta": {}}}),
        encoding="utf-8",
    )
    assert validate_mappings_layout() == 1


def test_validate_mappings_layout_errors_when_mappings_json_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_bundle_root(monkeypatch, tmp_path)
    (tmp_path / "policy").mkdir()
    (tmp_path / "providers.json").write_text(
        json.dumps({"providers": {"acme": _acme_row()}}),
        encoding="utf-8",
    )
    assert validate_mappings_layout() == 1


def test_validate_mappings_layout_skips_provider_field_check_for_non_json_mapped_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Mapped paths that do not end in .json skip the JSON provider-field check (line branch)."""
    _patch_bundle_root(monkeypatch, tmp_path)
    (tmp_path / "policy").mkdir()
    (tmp_path / "providers.json").write_text(
        json.dumps({"providers": {"acme": _acme_row()}}),
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
                            "schemas/placeholder.schema.json": "providers/acme/notes.txt",
                            "schemas/products.schema.json": "providers/acme/products.json",
                        }
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "providers" / "acme").mkdir(parents=True)
    (tmp_path / "providers" / "acme" / "notes.txt").write_text("x", encoding="utf-8")
    (tmp_path / "providers" / "acme" / "products.json").write_text(
        json.dumps({"provider": "acme", "products": []}),
        encoding="utf-8",
    )
    assert validate_mappings_layout() == 0


def test_validate_mappings_layout_ignores_nondirectory_entries_under_providers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_bundle_root(monkeypatch, tmp_path)
    (tmp_path / "policy").mkdir()
    (tmp_path / "providers.json").write_text(
        json.dumps({"providers": {"acme": _acme_row()}}),
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
                            "schemas/products.schema.json": "providers/acme/products.json",
                        }
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "providers" / "acme").mkdir(parents=True)
    (tmp_path / "providers" / "acme" / "products.json").write_text(
        json.dumps({"provider": "acme", "products": []}),
        encoding="utf-8",
    )
    (tmp_path / "providers" / "junk").write_text("", encoding="utf-8")
    assert validate_mappings_layout() == 0


def test_validate_mappings_layout_skips_dot_prefixed_provider_dirs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Hidden dirs under ``providers/`` (``.…``, ``__pycache__``) are not treated as provider ids."""
    _patch_bundle_root(monkeypatch, tmp_path)
    (tmp_path / "policy").mkdir()
    (tmp_path / "providers.json").write_text(
        json.dumps({"providers": {"acme": _acme_row()}}),
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
                            "schemas/products.schema.json": "providers/acme/products.json",
                        }
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "providers" / "acme").mkdir(parents=True)
    (tmp_path / "providers" / "acme" / "products.json").write_text(
        json.dumps({"provider": "acme", "products": []}),
        encoding="utf-8",
    )
    (tmp_path / "providers" / ".cache").mkdir()
    (tmp_path / "providers" / "__pycache__").mkdir()
    assert validate_mappings_layout() == 0


def test_validate_mappings_layout_warns_when_metadata_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _patch_bundle_root(monkeypatch, tmp_path)
    (tmp_path / "policy").mkdir()
    (tmp_path / "providers.json").write_text(
        json.dumps({"providers": {"acme": _acme_row()}}),
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
                            "schemas/products.schema.json": "providers/acme/products.json",
                        }
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "providers" / "acme").mkdir(parents=True)
    (tmp_path / "providers" / "acme" / "products.json").write_text(
        json.dumps({"provider": "acme", "products": []}),
        encoding="utf-8",
    )
    assert validate_mappings_layout() == 0
    assert "metadata.json" in capsys.readouterr().out
