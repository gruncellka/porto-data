#!/usr/bin/env python3
"""Tests for scripts.data_files project root resolution and helpers."""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts import data_files


def _fake_porto_data_module(prefix: Path, has_mappings: bool):
    """Return a fake porto_data module; __file__ under prefix, mappings.json if has_mappings."""
    if has_mappings:
        (prefix / "mappings.json").write_text("{}")
    mod = type(sys)("porto_data")
    mod.__file__ = str(prefix / "__init__.py")
    return mod


class TestGetProjectRoot:
    """Test get_project_root() / _get_project_root() resolution order and errors."""

    def test_returns_dev_root_when_mappings_at_repo_root(self, tmp_path):
        """When mappings.json exists at script_dir.parent (dev repo root), return it."""
        (tmp_path / "mappings.json").write_text("{}")
        fake_script = tmp_path / "scripts" / "data_files.py"
        fake_script.parent.mkdir(parents=True, exist_ok=True)
        # Fake porto_data without mappings so try 1 fails
        no_mappings = tmp_path / "no_mappings"
        no_mappings.mkdir()

        with (
            patch.object(data_files, "__file__", str(fake_script)),
            patch.dict("sys.modules", {"porto_data": _fake_porto_data_module(no_mappings, False)}),
        ):
            root = data_files.get_project_root()

        assert root == tmp_path
        assert (root / "mappings.json").exists()

    def test_returns_porto_data_subdir_when_mappings_under_porto_data(self, tmp_path):
        """When mappings.json is at dev_root/porto_data/, return that directory."""
        porto_data = tmp_path / "porto_data"
        porto_data.mkdir()
        (porto_data / "mappings.json").write_text("{}")
        fake_script = tmp_path / "scripts" / "data_files.py"
        fake_script.parent.mkdir(parents=True, exist_ok=True)
        no_mappings = tmp_path / "no_mappings"
        no_mappings.mkdir()

        with (
            patch.object(data_files, "__file__", str(fake_script)),
            patch.dict("sys.modules", {"porto_data": _fake_porto_data_module(no_mappings, False)}),
        ):
            root = data_files.get_project_root()

        assert root == porto_data
        assert (root / "mappings.json").exists()

    def test_returns_cwd_when_mappings_in_cwd(self, tmp_path):
        """When mappings.json is in current working directory only, return cwd."""
        (tmp_path / "mappings.json").write_text("{}")
        other = tmp_path / "other"
        other.mkdir()
        fake_script = other / "scripts" / "data_files.py"
        fake_script.parent.mkdir(parents=True, exist_ok=True)
        no_mappings = tmp_path / "no_mappings"
        no_mappings.mkdir()

        with (
            patch.object(data_files, "__file__", str(fake_script)),
            patch.dict(
                "sys.modules",
                {"porto_data": _fake_porto_data_module(no_mappings, False)},
            ),
            patch.object(Path, "cwd", return_value=tmp_path),
        ):
            root = data_files.get_project_root()

        assert root == tmp_path
        assert (root / "mappings.json").exists()

    def test_returns_cwd_porto_data_when_mappings_under_cwd_porto_data(self, tmp_path):
        """When mappings.json is in cwd/porto_data/, return cwd/porto_data."""
        porto_data = tmp_path / "porto_data"
        porto_data.mkdir()
        (porto_data / "mappings.json").write_text("{}")
        other = tmp_path / "other"
        other.mkdir()
        fake_script = other / "scripts" / "data_files.py"
        fake_script.parent.mkdir(parents=True, exist_ok=True)
        no_mappings = tmp_path / "no_mappings"
        no_mappings.mkdir()

        with (
            patch.object(data_files, "__file__", str(fake_script)),
            patch.dict(
                "sys.modules",
                {"porto_data": _fake_porto_data_module(no_mappings, False)},
            ),
            patch.object(Path, "cwd", return_value=tmp_path),
        ):
            root = data_files.get_project_root()

        assert root == porto_data
        assert (root / "mappings.json").exists()

    def test_raises_file_not_found_when_mappings_nowhere(self, tmp_path):
        """When mappings.json is not in any tried location, raise FileNotFoundError."""
        fake_script = tmp_path / "scripts" / "data_files.py"
        fake_script.parent.mkdir(parents=True, exist_ok=True)
        no_mappings = tmp_path / "no_mappings"
        no_mappings.mkdir()

        with (
            patch.object(data_files, "__file__", str(fake_script)),
            patch.dict(
                "sys.modules",
                {"porto_data": _fake_porto_data_module(no_mappings, False)},
            ),
            patch.object(Path, "cwd", return_value=tmp_path),
            pytest.raises(FileNotFoundError) as exc_info,
        ):
            data_files.get_project_root()

        msg = str(exc_info.value)
        assert "mappings.json not found" in msg
        assert "1." in msg or "porto_data" in msg
        assert "Run the CLI" in msg or "install the package" in msg

    def test_prefers_porto_data_package_when_importable_and_has_mappings(self, tmp_path):
        """When porto_data is importable and has mappings.json, return its directory."""
        fake_module = _fake_porto_data_module(tmp_path, has_mappings=True)

        with patch.dict("sys.modules", {"porto_data": fake_module}):
            root = data_files.get_project_root()

        assert root == tmp_path
        assert (root / "mappings.json").exists()

    def test_falls_through_to_dev_root_when_porto_data_has_no_mappings(self, tmp_path):
        """When porto_data is importable but has no mappings.json there, use try 2 (dev root)."""
        no_mappings = tmp_path / "no_mappings"
        no_mappings.mkdir()
        (tmp_path / "scripts").mkdir(parents=True, exist_ok=True)
        (tmp_path / "mappings.json").write_text("{}")
        fake_module = _fake_porto_data_module(no_mappings, has_mappings=False)

        with (
            patch.object(data_files, "__file__", str(tmp_path / "scripts" / "data_files.py")),
            patch.dict("sys.modules", {"porto_data": fake_module}),
        ):
            root = data_files.get_project_root()

        assert root == tmp_path
        assert (root / "mappings.json").exists()

    def test_get_project_root_handles_import_error(self, tmp_path):
        """When import porto_data raises ImportError, fall through to try 2 (dev root)."""
        (tmp_path / "mappings.json").write_text("{}")
        (tmp_path / "scripts").mkdir(parents=True, exist_ok=True)
        import builtins

        real_import = builtins.__import__

        def raise_for_porto_data(name, *args, **kwargs):
            if name == "porto_data":
                raise ImportError("No module named 'porto_data'")
            return real_import(name, *args, **kwargs)

        with (
            patch.object(data_files, "__file__", str(tmp_path / "scripts" / "data_files.py")),
            patch("builtins.__import__", side_effect=raise_for_porto_data),
        ):
            root = data_files.get_project_root()
        assert root == tmp_path
        assert (root / "mappings.json").exists()


class TestLoadMappingsUsesProjectRoot:
    """Test that load_mappings(None) uses get_project_root to find mappings."""

    def test_load_mappings_without_path_uses_project_root(self, tmp_path):
        """When mappings_path is None, load from project root (e.g. cwd with mappings)."""
        mappings_data = {
            "mappings": {
                "schemas/products.schema.json": "data/products.json",
            }
        }
        (tmp_path / "mappings.json").write_text(json.dumps(mappings_data))
        fake_script = tmp_path / "scripts" / "data_files.py"
        fake_script.parent.mkdir(parents=True, exist_ok=True)
        no_mappings = tmp_path / "no_mappings"
        no_mappings.mkdir()

        with (
            patch.object(data_files, "__file__", str(fake_script)),
            patch.dict("sys.modules", {"porto_data": _fake_porto_data_module(no_mappings, False)}),
        ):
            result = data_files.load_mappings(mappings_path=None)

        assert "schemas/products.schema.json" in result
        assert result["schemas/products.schema.json"] == "data/products.json"


class TestConstantsAndHelpers:
    """Test bundle mapping keys, PROVIDERS_DIR, get_global_data_paths, get_provider_data_paths."""

    def test_bundle_mapping_keys_and_providers_dir_constants(self):
        """Policy/formats/registry keys and PROVIDERS_DIR match mappings.json / metadata.json."""
        assert data_files.POLICY_MAPPINGS_KEY == "policy"
        assert data_files.FORMATS_MAPPINGS_KEY == "formats"
        assert data_files.REGISTRY_MAPPINGS_KEY == "registry"
        assert data_files.PROVIDERS_DIR == "providers"

    def test_get_global_data_paths_returns_dict(self):
        """get_global_data_paths returns entity name -> path mapping."""
        result = data_files.get_global_data_paths()
        assert isinstance(result, dict)
        # Non-provider paths: policy/, formats/, or providers.json at bundle root
        for key, val in result.items():
            assert isinstance(key, str)
            assert isinstance(val, str)
            assert (
                val.startswith("policy/")
                or val.startswith("formats/")
                or val == data_files.PROVIDERS_REGISTRY_FILENAME
            )

    def test_get_provider_data_paths_returns_dict(self):
        """get_provider_data_paths returns entity name -> path for provider."""
        result = data_files.get_provider_data_paths("deutschepost")
        assert isinstance(result, dict)
        for key, val in result.items():
            assert isinstance(key, str)
            assert isinstance(val, str)
            assert "providers/deutschepost/" in val

    def test_get_provider_data_paths_unknown_provider_returns_empty(self):
        """get_provider_data_paths for unknown provider returns empty dict."""
        result = data_files.get_provider_data_paths("nonexistent_provider_xyz")
        assert result == {}

    def test_get_global_data_paths_with_malformed_global_returns_empty(self, tmp_path):
        """When a bundle block is not a dict, get_global_data_paths skips it."""
        (tmp_path / "mappings.json").write_text(
            json.dumps(
                {
                    "mappings": {
                        "policy": "not_a_dict",
                        "formats": {},
                        "registry": {},
                        "providers": {
                            "deutschepost": {
                                "schemas/products.schema.json": "providers/deutschepost/products.json"
                            }
                        },
                    }
                }
            )
        )
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            result = data_files.get_global_data_paths()
        assert result == {}

    def test_get_provider_data_paths_with_malformed_provider_mappings_returns_empty(self, tmp_path):
        """When provider mappings is not a dict, get_provider_data_paths returns empty."""
        (tmp_path / "mappings.json").write_text(
            json.dumps(
                {
                    "mappings": {
                        "policy": {},
                        "formats": {},
                        "registry": {},
                        "providers": {"deutschepost": "not_a_dict"},
                    }
                }
            )
        )
        with patch.object(data_files, "_get_project_root", return_value=tmp_path):
            result = data_files.get_provider_data_paths("deutschepost")
        assert result == {}


class TestListProviderIds:
    """list_provider_ids() from mappings."""

    def test_includes_laposte_swisspost_deutschepost(self):
        ids = data_files.list_provider_ids()
        assert ids == ["deutschepost", "ukrposhta", "laposte", "swisspost"]
        assert "deutschepost" in ids
        assert "swisspost" in ids
        assert "laposte" in ids
        assert "ukrposhta" in ids


class TestLoadProvidersRegistryErrors:
    def test_raises_file_not_found_when_registry_missing(self, tmp_path):
        with (
            patch.object(data_files, "_get_project_root", return_value=tmp_path),
            pytest.raises(FileNotFoundError, match="Provider registry not found"),
        ):
            data_files.load_providers_registry()

    def test_raises_value_error_when_providers_empty(self, tmp_path):
        (tmp_path / "providers.json").write_text(json.dumps({"providers": {}}), encoding="utf-8")
        with (
            patch.object(data_files, "_get_project_root", return_value=tmp_path),
            pytest.raises(ValueError, match="non-empty object 'providers'"),
        ):
            data_files.load_providers_registry()


class TestGetMappingsProviderIdsEdgeCases:
    def test_returns_empty_when_providers_section_not_dict(self, tmp_path):
        (tmp_path / "mappings.json").write_text(
            json.dumps({"mappings": {"providers": []}}), encoding="utf-8"
        )
        assert data_files.get_mappings_provider_ids(str(tmp_path / "mappings.json")) == set()

    def test_returns_provider_ids_from_valid_mappings_file(self, tmp_path):
        (tmp_path / "mappings.json").write_text(
            json.dumps(
                {
                    "mappings": {
                        "providers": {
                            "alpha": {"schemas/x.schema.json": "providers/a/p.json"},
                            "beta": {"schemas/y.schema.json": "providers/b/p.json"},
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        ids = data_files.get_mappings_provider_ids(str(tmp_path / "mappings.json"))
        assert ids == {"alpha", "beta"}


class TestGetDataFilePathProjectRoot:
    def test_resolves_limits_relative_to_given_root(self, tmp_path):
        (tmp_path / "policy").mkdir()
        (tmp_path / "providers.json").write_text(
            json.dumps(
                {
                    "providers": {
                        "acme": {
                            "name": "A",
                            "country": "XX",
                            "mark_types": ["stamp"],
                            "tracking_model": "mixed",
                        }
                    }
                }
            ),
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
        p = data_files.get_data_file_path("limits", "acme", project_root=tmp_path)
        assert p == tmp_path / "providers" / "acme" / "limits.json"
