"""Shared fixtures and utilities for all tests."""

import json
from pathlib import Path

import pytest

_project_root = Path(__file__).parent.parent
_scripts_path = _project_root / "scripts"


@pytest.fixture
def project_root():
    """Return project root path."""
    return _project_root


@pytest.fixture
def scripts_path():
    """Return scripts directory path."""
    return _scripts_path


@pytest.fixture
def minimal_data_links():
    """Minimal valid data_links.json structure."""
    return {
        "file_type": "data_links",
        "schema_version": "1.0",
        "unit": {"weight": "g", "dimension": "mm", "price": "cents", "currency": "EUR"},
        "dependencies": {},
        "links": {},
        "global_settings": {
            "price_source": "prices.json",
            "lookup_method": {"file": "prices.json", "array": "prices.product_prices", "match": {}},
            "available_services": [],
        },
    }


@pytest.fixture
def minimal_services():
    """Minimal valid services.json structure."""
    return {
        "file_type": "services",
        "services": [],
    }


@pytest.fixture
def minimal_prices():
    """Minimal valid prices.json structure."""
    return {
        "file_type": "prices",
        "unit": {"price": "cents", "currency": "EUR"},
        "prices": {
            "product_prices": [],
            "service_prices": [],
        },
    }


@pytest.fixture
def minimal_data_files(tmp_path, minimal_services, minimal_prices, minimal_data_links):
    """Create minimal data files structure for testing."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # Create all required data files
    files = {
        "services.json": minimal_services,
        "prices.json": minimal_prices,
        "data_links.json": minimal_data_links,
        "products.json": {"products": [], "file_type": "products"},
        "zones.json": {"zones": [], "file_type": "zones"},
        "weight_tiers.json": {"weight_tiers": {}, "file_type": "weight_tiers"},
        "dimensions.json": {"dimensions": {}, "file_type": "dimensions"},
        "features.json": {"features": {}, "file_type": "features"},
        "restrictions.json": {"restrictions": [], "file_type": "restrictions"},
    }

    for filename, data in files.items():
        with open(data_dir / filename, "w") as f:
            json.dump(data, f)

    return data_dir


@pytest.fixture
def sample_schema():
    """Sample JSON schema for testing."""
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
        },
        "required": ["name"],
    }


@pytest.fixture
def sample_valid_data():
    """Sample valid JSON data matching sample_schema."""
    return {"name": "Test", "age": 30}


@pytest.fixture
def sample_invalid_data():
    """Sample invalid JSON data (missing required field)."""
    return {"age": 30}  # Missing "name"


def create_test_data_files(tmp_path, **file_data):
    """Helper to create test data files with custom data.

    Args:
        tmp_path: pytest tmp_path fixture
        **file_data: Keyword arguments where key is filename and value is data dict

    Returns:
        Path to data directory
    """
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # Default minimal files
    defaults = {
        "products.json": {"products": [], "file_type": "products"},
        "zones.json": {"zones": [], "file_type": "zones"},
        "weight_tiers.json": {"weight_tiers": {}, "file_type": "weight_tiers"},
        "dimensions.json": {"dimensions": {}, "file_type": "dimensions"},
        "features.json": {"features": {}, "file_type": "features"},
        "restrictions.json": {"restrictions": [], "file_type": "restrictions"},
    }

    # Merge defaults with provided data
    all_files = {**defaults, **file_data}

    for filename, data in all_files.items():
        with open(data_dir / filename, "w") as f:
            json.dump(data, f)

    return data_dir
