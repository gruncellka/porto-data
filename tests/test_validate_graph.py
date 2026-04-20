#!/usr/bin/env python3
"""Tests for graph validation (scripts.validators.graph)."""

import json
from pathlib import Path

import pytest

from scripts.validators.base import ValidationResults
from scripts.validators.graph import GraphValidator
from tests.minimal_fixtures import minimal_restrictions_document


class TestGraphValidatorInitialization:
    """Test GraphValidator initialization and error handling."""

    def test_validator_initialization_with_project_root(self, project_root):
        """Test validator with project_root + provider (policy/, mails/, providers/)."""
        from scripts.data_files import POLICY_MAPPINGS_KEY, PROVIDERS_DIR

        porto_data = project_root / "porto_data"
        if not (porto_data / PROVIDERS_DIR).exists():
            pytest.skip("porto_data providers/ not found")
        if not (porto_data / "policy").exists():
            pytest.skip("porto_data policy/ not found")
        validator = GraphValidator(project_root=porto_data, provider="deutschepost")
        assert validator.shared_bundle_subdir == porto_data / POLICY_MAPPINGS_KEY
        assert validator.provider_dir == porto_data / PROVIDERS_DIR / "deutschepost"
        validator.load_data()
        assert validator.graph is not None
        assert validator.envelopes is not None

    def test_validator_initialization_success(self, minimal_data_files):
        """Test that validator can be initialized with valid directory."""
        validator = GraphValidator(minimal_data_files)
        assert validator.data_dir == minimal_data_files
        assert isinstance(validator.results, dict)
        assert all(
            key in validator.results for key in ["errors", "warnings", "fixes_needed", "correct"]
        )

    def test_validator_initialization_fails_invalid_path(self):
        """Test that validator raises error for invalid path."""
        invalid_path = Path("/nonexistent/path")
        with pytest.raises(FileNotFoundError, match="does not exist"):
            GraphValidator(invalid_path)

    def test_validator_initialization_fails_file_not_dir(self, tmp_path):
        """Test that validator raises error if path is a file, not directory."""
        file_path = tmp_path / "not_a_dir.txt"
        file_path.write_text("test")
        with pytest.raises(ValueError, match="not a directory"):
            GraphValidator(file_path)

    def test_validator_loads_data(self, minimal_data_files):
        """Test that validator can load data files."""
        validator = GraphValidator(minimal_data_files)
        validator.load_data()

        assert validator.graph is not None
        assert validator.products is not None
        assert validator.zones is not None
        assert isinstance(validator.product_dict, dict)

    def test_load_data_reports_missing_file(self, tmp_path, minimal_graph):
        """Test that load_data adds an error when a required file is missing."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        (data_dir / "graph.json").write_text(json.dumps(minimal_graph))
        # Omit products.json and others so load_json raises FileNotFoundError
        validator = GraphValidator(data_dir)
        validator.load_data()
        assert len(validator.results["errors"]) >= 1
        assert (
            "Missing file" in validator.results["errors"][0]
            or "file" in validator.results["errors"][0].lower()
        )


class TestGraphValidatorResults:
    """Test GraphValidator results structure and validation."""

    def test_validate_all_returns_validation_results(self, minimal_data_files):
        """Test that validate_all returns ValidationResults."""
        validator = GraphValidator(minimal_data_files)
        results = validator.validate_all()

        assert isinstance(results, dict)
        assert all(key in results for key in ["errors", "warnings", "fixes_needed", "correct"])
        assert all(isinstance(v, list) for v in results.values())

    def test_results_structure_matches_typedict(self, minimal_data_files):
        """Test that results match ValidationResults TypedDict."""
        validator = GraphValidator(minimal_data_files)
        results = validator.validate_all()

        # Type check - should match ValidationResults structure
        typed_results: ValidationResults = results
        assert isinstance(typed_results["errors"], list)
        assert isinstance(typed_results["warnings"], list)
        assert isinstance(typed_results["fixes_needed"], list)
        assert isinstance(typed_results["correct"], list)


class TestServicePriceConsistency:
    """Test service-price effective date consistency validation."""

    @pytest.fixture
    def service_data_template(self):
        """Template for service data."""
        return {
            "id": "test_service",
            "porto_id": "test_service",
            "name": "Test Service",
            "label": "Test service",
            "description": "A test service",
            "features": ["tracking"],
        }

    @pytest.fixture
    def price_data_template(self):
        """Template for service price data."""
        return {
            "file_type": "service_prices",
            "provider": "deutschepost",
            "unit": {"price": "cents", "currency": "EUR"},
            "service_prices": [
                {
                    "service_id": "test_service",
                    "price": [{"amount": 100, "effective_from": None, "effective_to": None}],
                }
            ],
        }

    def create_test_scenario(self, tmp_path, service_effective_to, price_effective_to):
        """Helper to create test scenario with specific effective_to values."""

        data_dir = tmp_path / "data"
        data_dir.mkdir()

        services_data = {
            "file_type": "services",
            "services": [
                {
                    "id": "test_service",
                    "porto_id": "test_service",
                    "name": "Test Service",
                    "label": "Test service",
                    "description": "A test service",
                    "features": ["tracking"],
                    **({"effective_to": service_effective_to} if service_effective_to else {}),
                }
            ],
        }

        prices_data = {
            "file_type": "service_prices",
            "provider": "deutschepost",
            "unit": {"price": "cents", "currency": "EUR"},
            "service_prices": [
                {
                    "service_id": "test_service",
                    "price": [
                        {
                            "amount": 100,
                            "effective_from": None,
                            "effective_to": price_effective_to,
                        }
                    ],
                }
            ],
        }

        product_prices_data = {
            "file_type": "product_prices",
            "provider": "deutschepost",
            "unit": {"price": "cents", "currency": "EUR"},
            "product_prices": [],
        }

        graph_data = {
            "file_type": "graph",
            "provider": "deutschepost",
            "unit": {"weight": "g", "dimension": "mm", "price": "cents", "currency": "EUR"},
            "dependencies": {},
            "edges": {},
            "lookup_rules": {},
            "global_settings": {
                "price_lookup": {
                    "product_prices": {
                        "file": "prices/products.json",
                        "array": "product_prices",
                        "match": {},
                        "description": "test",
                    },
                    "service_prices": {
                        "file": "prices/services.json",
                        "array": "service_prices",
                        "match": {},
                        "description": "test",
                    },
                },
                "available_services": [],
            },
        }

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
                        "sheets": [
                            {"sheet": "A4", "fold": "quarter", "description": "Test fixture"}
                        ],
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
                                    "print_area": {"x": 0, "y": 0, "width": 100, "height": 80},
                                    "address_area": {"x": 0, "y": 0, "width": 100, "height": 80},
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
                    {"id": "test_stamp", "mark_type": "stamp", "label": "Test stamp profile"}
                ],
            },
            "restrictions.json": minimal_restrictions_document(),
        }

        prices_dir = data_dir / "prices"
        prices_dir.mkdir(parents=True, exist_ok=True)
        all_files = {**defaults, "services.json": services_data, "graph.json": graph_data}
        for filename, data in all_files.items():
            with open(data_dir / filename, "w") as f:
                json.dump(data, f)
        with open(prices_dir / "services.json", "w") as f:
            json.dump(prices_data, f)
        with open(prices_dir / "products.json", "w") as f:
            json.dump(product_prices_data, f)

        return data_dir

    @pytest.mark.parametrize(
        "service_effective_to,price_effective_to,should_pass,error_keywords",
        [
            # Both have matching effective_to - should pass
            ("2024-12-31", "2024-12-31", True, []),
            # Both are active (no effective_to) - should pass
            (None, None, True, []),
            # Price has effective_to but service doesn't - should fail
            (None, "2024-12-31", False, ["effective_to", "discontinued"]),
            # Mismatched dates - should fail
            ("2024-12-30", "2024-12-31", False, ["match", "effective_to"]),
        ],
    )
    def test_service_price_consistency_scenarios(
        self, tmp_path, service_effective_to, price_effective_to, should_pass, error_keywords
    ):
        """Test service-price consistency with various scenarios."""
        data_dir = self.create_test_scenario(tmp_path, service_effective_to, price_effective_to)
        validator = GraphValidator(data_dir)
        results = validator.validate_all()

        # Check for service-price related errors
        if error_keywords:
            service_price_errors = [
                e
                for e in results["errors"]
                if any(keyword in e.lower() for keyword in error_keywords) or "test_service" in e
            ]
        else:
            # For passing cases, check that there are no service-price errors
            service_price_errors = [
                e
                for e in results["errors"]
                if "effective_to" in e.lower() or "discontinued" in e.lower() or "test_service" in e
            ]

        if should_pass:
            assert len(service_price_errors) == 0, f"Unexpected errors: {service_price_errors}"
        else:
            assert len(service_price_errors) > 0, (
                f"Should have detected service-price inconsistency. All errors: {results['errors']}"
            )
            assert any("test_service" in e for e in service_price_errors), (
                "Error should mention service ID"
            )

    def test_missing_service_in_services_json_fails(self, tmp_path, minimal_graph):
        """Test that price referencing non-existent service fails validation."""

        data_dir = tmp_path / "data"
        data_dir.mkdir()

        services_data = {"file_type": "services", "services": []}  # No services

        prices_data = {
            "file_type": "service_prices",
            "provider": "deutschepost",
            "unit": {"price": "cents", "currency": "EUR"},
            "service_prices": [
                {
                    "service_id": "nonexistent_service",
                    "price": [
                        {"amount": 100, "effective_from": None, "effective_to": "2024-12-31"}
                    ],
                }
            ],
        }

        product_prices_data = {
            "file_type": "product_prices",
            "provider": "deutschepost",
            "unit": {"price": "cents", "currency": "EUR"},
            "product_prices": [],
        }

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
                        "sheets": [
                            {"sheet": "A4", "fold": "quarter", "description": "Test fixture"}
                        ],
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
                                    "print_area": {"x": 0, "y": 0, "width": 100, "height": 80},
                                    "address_area": {"x": 0, "y": 0, "width": 100, "height": 80},
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
                    {"id": "test_stamp", "mark_type": "stamp", "label": "Test stamp profile"}
                ],
            },
            "restrictions.json": minimal_restrictions_document(),
        }

        prices_dir = data_dir / "prices"
        prices_dir.mkdir(parents=True, exist_ok=True)
        all_files = {**defaults, "services.json": services_data, "graph.json": minimal_graph}
        for filename, data in all_files.items():
            with open(data_dir / filename, "w") as f:
                json.dump(data, f)
        with open(prices_dir / "services.json", "w") as f:
            json.dump(prices_data, f)
        with open(prices_dir / "products.json", "w") as f:
            json.dump(product_prices_data, f)
        validator = GraphValidator(data_dir)
        results = validator.validate_all()

        # Should have an error about missing service
        missing_service_errors = [
            e for e in results["errors"] if "nonexistent_service" in e and "not found" in e.lower()
        ]
        assert len(missing_service_errors) > 0, "Should have detected missing service"


class TestGraphValidatorImports:
    """Imports for graph validation."""

    def test_validator_importable_from_graph_module(self, minimal_data_files):
        """GraphValidator is importable from scripts.validators.graph."""
        from scripts.validators.graph import GraphValidator as Import

        validator = Import(minimal_data_files)
        assert validator.__class__.__name__ == "GraphValidator"
        assert hasattr(validator, "validate_all")

    def test_validation_results_importable_from_base(self):
        """Test that ValidationResults can be imported from scripts.validators."""
        from scripts.validators.base import ValidationResults as Import

        results: Import = {
            "errors": [],
            "warnings": [],
            "fixes_needed": [],
            "correct": [],
        }
        assert isinstance(results, dict)
