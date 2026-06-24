"""Shared fixtures and utilities for all tests."""

import json
from pathlib import Path

import pytest

from tests.minimal_fixtures import minimal_restrictions_document

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
def minimal_graph():
    """Minimal valid graph.json structure."""
    return {
        "file_type": "graph",
        "provider": "deutschepost",
        "unit": {"weight": "g", "dimension": "mm", "price": "cents", "currency": "EUR"},
        "dependencies": {},
        "edges": {"products": {}, "marks": {}},
        "services": ["einschreiben"],
    }


@pytest.fixture
def minimal_services():
    """Minimal valid services.json structure."""
    return {
        "file_type": "services",
        "services": [],
    }


@pytest.fixture
def minimal_product_prices():
    """Minimal valid product_prices.json structure."""
    return {
        "file_type": "product_prices",
        "provider": "deutschepost",
        "unit": {"price": "cents", "currency": "EUR"},
        "product_prices": [],
    }


@pytest.fixture
def minimal_service_prices():
    """Minimal valid service_prices.json structure."""
    return {
        "file_type": "service_prices",
        "provider": "deutschepost",
        "unit": {"price": "cents", "currency": "EUR"},
        "service_prices": [],
    }


@pytest.fixture
def minimal_envelope_layouts():
    """Minimal layouts.json (DE C6 only, matches minimal envelopes fixture)."""
    return {
        "file_type": "layouts",
        "unit": {"dimension": "mm"},
        "jurisdictions": {
            "DE": {
                "envelopes": {
                    "C6": {
                        "orientation": "landscape",
                        "layout": {
                            "window": {"supported": False},
                            "post_mark": {"x": 90, "y": 5},
                        },
                    }
                }
            }
        },
    }


@pytest.fixture
def minimal_data_files(
    tmp_path,
    minimal_services,
    minimal_product_prices,
    minimal_service_prices,
    minimal_graph,
    minimal_envelope_layouts,
):
    """Create minimal data files structure for testing."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    prices_dir = data_dir / "prices"
    prices_dir.mkdir()

    files = {
        "services.json": minimal_services,
        "graph.json": minimal_graph,
        "products.json": {"products": [], "file_type": "products"},
        "zones.json": {"zones": [], "file_type": "zones"},
        "weights.json": {"weights": {}, "file_type": "weights"},
        "envelopes.json": {
            "file_type": "envelopes",
            "unit": {"dimension": "mm"},
            "envelopes": [
                {
                    "id": "C6",
                    "label": "C6",
                    "width": 162,
                    "height": 114,
                    "standard": "ISO269",
                    "sheets": [{"sheet": "A4", "fold": "quarter", "description": "Test fixture"}],
                }
            ],
        },
        "layouts.json": minimal_envelope_layouts,
        "features.json": {
            "file_type": "features",
            "provider": "deutschepost",
            "features": [
                {
                    "id": "tracking_number",
                    "porto_id": "tracking_number",
                    "name": "Sendungsnummer",
                    "label": "Tracking number",
                    "description": "Test",
                }
            ],
        },
        "marks.json": {
            "file_type": "marks",
            "provider": "deutschepost",
            "default_profile": "test_stamp",
            "profiles": [
                {
                    "id": "test_stamp",
                    "mark_type": "stamp",
                    "label": "Test stamp profile",
                }
            ],
        },
        "restrictions.json": minimal_restrictions_document(),
    }

    for filename, data in files.items():
        with open(data_dir / filename, "w") as f:
            json.dump(data, f)

    with open(prices_dir / "products.json", "w") as f:
        json.dump(minimal_product_prices, f)
    with open(prices_dir / "services.json", "w") as f:
        json.dump(minimal_service_prices, f)

    return data_dir


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

    prices_dir = data_dir / "prices"
    prices_dir.mkdir()

    defaults = {
        "products.json": {"products": [], "file_type": "products"},
        "zones.json": {"zones": [], "file_type": "zones"},
        "weights.json": {"weights": {}, "file_type": "weights"},
        "envelopes.json": {
            "file_type": "envelopes",
            "unit": {"dimension": "mm"},
            "envelopes": [
                {
                    "id": "C6",
                    "label": "C6",
                    "width": 162,
                    "height": 114,
                    "standard": "ISO269",
                    "sheets": [{"sheet": "A4", "fold": "quarter", "description": "Test fixture"}],
                }
            ],
        },
        "layouts.json": {
            "file_type": "layouts",
            "unit": {"dimension": "mm"},
            "jurisdictions": {
                "DE": {
                    "envelopes": {
                        "C6": {
                            "orientation": "landscape",
                            "layout": {
                                "window": {"supported": False},
                                "post_mark": {"x": 90, "y": 5},
                            },
                        }
                    }
                }
            },
        },
        "features.json": {
            "file_type": "features",
            "provider": "deutschepost",
            "features": [
                {
                    "id": "tracking_number",
                    "porto_id": "tracking_number",
                    "name": "Sendungsnummer",
                    "label": "Tracking number",
                    "description": "Test",
                }
            ],
        },
        "marks.json": {
            "file_type": "marks",
            "provider": "deutschepost",
            "default_profile": "test_stamp",
            "profiles": [
                {
                    "id": "test_stamp",
                    "mark_type": "stamp",
                    "label": "Test stamp profile",
                }
            ],
        },
        "restrictions.json": minimal_restrictions_document(),
    }

    all_files = {**defaults, **file_data}
    pp = all_files.pop("product_prices.json", None)
    sp = all_files.pop("service_prices.json", None)
    if pp is None:
        pp = {
            "file_type": "product_prices",
            "provider": "deutschepost",
            "unit": {"price": "cents", "currency": "EUR"},
            "product_prices": [],
        }
    if sp is None:
        sp = {
            "file_type": "service_prices",
            "provider": "deutschepost",
            "unit": {"price": "cents", "currency": "EUR"},
            "service_prices": [],
        }

    for filename, data in all_files.items():
        with open(data_dir / filename, "w") as f:
            json.dump(data, f)

    with open(prices_dir / "products.json", "w") as f:
        json.dump(pp, f)
    with open(prices_dir / "services.json", "w") as f:
        json.dump(sp, f)

    return data_dir
