#!/usr/bin/env python3
"""Tests for providers.json registry and validation."""

from scripts.data_files import (
    get_data_files,
    list_provider_ids,
    load_providers_registry,
)
from scripts.validators.providers_registry import validate_providers_registry


class TestLoadProvidersRegistry:
    def test_list_matches_three_providers(self):
        ids = list_provider_ids()
        assert ids == ["deutschepost", "laposte", "swisspost"]

    def test_laposte_coarse_metadata(self):
        doc = load_providers_registry()
        lp = doc["providers"]["laposte"]
        assert lp["country"] == "FR"
        assert lp["mark_types"] == ["label"]
        assert lp["tracking_model"] == "included"


class TestGetDataFiles:
    def test_providers_json_not_in_resolution_dependency_set(self):
        assert "providers.json" not in get_data_files()


class TestValidateProvidersRegistry:
    def test_real_tree_passes(self):
        assert validate_providers_registry() == 0
