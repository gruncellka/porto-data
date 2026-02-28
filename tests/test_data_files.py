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

        with patch.object(data_files, "__file__", str(fake_script)):
            with patch.dict("sys.modules", {"porto_data": _fake_porto_data_module(no_mappings, False)}):
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

        with patch.object(data_files, "__file__", str(fake_script)):
            with patch.dict("sys.modules", {"porto_data": _fake_porto_data_module(no_mappings, False)}):
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

        with patch.object(data_files, "__file__", str(fake_script)):
            with patch.dict("sys.modules", {"porto_data": _fake_porto_data_module(no_mappings, False)}):
                with patch.object(Path, "cwd", return_value=tmp_path):
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

        with patch.object(data_files, "__file__", str(fake_script)):
            with patch.dict("sys.modules", {"porto_data": _fake_porto_data_module(no_mappings, False)}):
                with patch.object(Path, "cwd", return_value=tmp_path):
                    root = data_files.get_project_root()

        assert root == porto_data
        assert (root / "mappings.json").exists()

    def test_raises_file_not_found_when_mappings_nowhere(self, tmp_path):
        """When mappings.json is not in any tried location, raise FileNotFoundError."""
        fake_script = tmp_path / "scripts" / "data_files.py"
        fake_script.parent.mkdir(parents=True, exist_ok=True)
        no_mappings = tmp_path / "no_mappings"
        no_mappings.mkdir()

        with patch.object(data_files, "__file__", str(fake_script)):
            with patch.dict("sys.modules", {"porto_data": _fake_porto_data_module(no_mappings, False)}):
                with patch.object(Path, "cwd", return_value=tmp_path):
                    with pytest.raises(FileNotFoundError) as exc_info:
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

        with patch.object(data_files, "__file__", str(fake_script)):
            with patch.dict("sys.modules", {"porto_data": _fake_porto_data_module(no_mappings, False)}):
                result = data_files.load_mappings(mappings_path=None)

        assert "schemas/products.schema.json" in result
        assert result["schemas/products.schema.json"] == "data/products.json"