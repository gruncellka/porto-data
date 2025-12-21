#!/usr/bin/env python3
"""Tests for data links validation - validators/links.py and backward compatibility."""

import json
from pathlib import Path

import pytest

from scripts.validators.base import ValidationResults
from scripts.validators.links import DataLinksValidator


class TestDataLinksValidatorInitialization:
    """Test DataLinksValidator initialization and error handling."""

    def test_validator_initialization_success(self, minimal_data_files):
        """Test that validator can be initialized with valid directory."""
        validator = DataLinksValidator(minimal_data_files)
        assert validator.data_dir == minimal_data_files
        assert isinstance(validator.results, dict)
        assert all(
            key in validator.results for key in ["errors", "warnings", "fixes_needed", "correct"]
        )

    def test_validator_initialization_fails_invalid_path(self):
        """Test that validator raises error for invalid path."""
        invalid_path = Path("/nonexistent/path")
        with pytest.raises(FileNotFoundError, match="does not exist"):
            DataLinksValidator(invalid_path)

    def test_validator_initialization_fails_file_not_dir(self, tmp_path):
        """Test that validator raises error if path is a file, not directory."""
        file_path = tmp_path / "not_a_dir.txt"
        file_path.write_text("test")
        with pytest.raises(ValueError, match="not a directory"):
            DataLinksValidator(file_path)

    def test_validator_loads_data(self, minimal_data_files):
        """Test that validator can load data files."""
        validator = DataLinksValidator(minimal_data_files)
        validator.load_data()

        assert validator.data_links is not None
        assert validator.products is not None
        assert validator.zones is not None
        assert isinstance(validator.product_dict, dict)


class TestDataLinksValidatorResults:
    """Test DataLinksValidator results structure and validation."""

    def test_validate_all_returns_validation_results(self, minimal_data_files):
        """Test that validate_all returns ValidationResults."""
        validator = DataLinksValidator(minimal_data_files)
        results = validator.validate_all()

        assert isinstance(results, dict)
        assert all(key in results for key in ["errors", "warnings", "fixes_needed", "correct"])
        assert all(isinstance(v, list) for v in results.values())

    def test_results_structure_matches_typedict(self, minimal_data_files):
        """Test that results match ValidationResults TypedDict."""
        validator = DataLinksValidator(minimal_data_files)
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
            "name": "Test Service",
            "description": "A test service",
            "features": ["tracking"],
        }

    @pytest.fixture
    def price_data_template(self):
        """Template for price data."""
        return {
            "file_type": "prices",
            "unit": {"price": "cents", "currency": "EUR"},
            "prices": {
                "service_prices": [
                    {
                        "service_id": "test_service",
                        "price": [{"price": 100, "effective_from": None, "effective_to": None}],
                    }
                ],
            },
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
                    "name": "Test Service",
                    "description": "A test service",
                    "features": ["tracking"],
                    **({"effective_to": service_effective_to} if service_effective_to else {}),
                }
            ],
        }

        prices_data = {
            "file_type": "prices",
            "unit": {"price": "cents", "currency": "EUR"},
            "prices": {
                "service_prices": [
                    {
                        "service_id": "test_service",
                        "price": [
                            {
                                "price": 100,
                                "effective_from": None,
                                "effective_to": price_effective_to,
                            }
                        ],
                    }
                ],
            },
        }

        data_links_data = {
            "file_type": "data_links",
            "schema_version": "1.0",
            "unit": {"weight": "g", "dimension": "mm", "price": "cents", "currency": "EUR"},
            "dependencies": {},
            "links": {},
            "global_settings": {
                "price_source": "prices.json",
                "lookup_method": {
                    "file": "prices.json",
                    "array": "prices.product_prices",
                    "match": {},
                },
                "available_services": [],
            },
        }

        # Create all required files
        defaults = {
            "products.json": {"products": [], "file_type": "products"},
            "zones.json": {"zones": [], "file_type": "zones"},
            "weight_tiers.json": {"weight_tiers": {}, "file_type": "weight_tiers"},
            "dimensions.json": {"dimensions": {}, "file_type": "dimensions"},
            "features.json": {"features": {}, "file_type": "features"},
            "restrictions.json": {"restrictions": [], "file_type": "restrictions"},
        }

        all_files = {
            **defaults,
            "services.json": services_data,
            "prices.json": prices_data,
            "data_links.json": data_links_data,
        }

        for filename, data in all_files.items():
            with open(data_dir / filename, "w") as f:
                json.dump(data, f)

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
        validator = DataLinksValidator(data_dir)
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

    def test_missing_service_in_services_json_fails(self, tmp_path, minimal_data_links):
        """Test that price referencing non-existent service fails validation."""

        data_dir = tmp_path / "data"
        data_dir.mkdir()

        services_data = {"file_type": "services", "services": []}  # No services

        prices_data = {
            "file_type": "prices",
            "unit": {"price": "cents", "currency": "EUR"},
            "prices": {
                "service_prices": [
                    {
                        "service_id": "nonexistent_service",
                        "price": [
                            {"price": 100, "effective_from": None, "effective_to": "2024-12-31"}
                        ],
                    }
                ],
            },
        }

        # Create all required files
        defaults = {
            "products.json": {"products": [], "file_type": "products"},
            "zones.json": {"zones": [], "file_type": "zones"},
            "weight_tiers.json": {"weight_tiers": {}, "file_type": "weight_tiers"},
            "dimensions.json": {"dimensions": {}, "file_type": "dimensions"},
            "features.json": {"features": {}, "file_type": "features"},
            "restrictions.json": {"restrictions": [], "file_type": "restrictions"},
        }

        all_files = {
            **defaults,
            "services.json": services_data,
            "prices.json": prices_data,
            "data_links.json": minimal_data_links,
        }

        for filename, data in all_files.items():
            with open(data_dir / filename, "w") as f:
                json.dump(data, f)
        validator = DataLinksValidator(data_dir)
        results = validator.validate_all()

        # Should have an error about missing service
        missing_service_errors = [
            e for e in results["errors"] if "nonexistent_service" in e and "not found" in e.lower()
        ]
        assert len(missing_service_errors) > 0, "Should have detected missing service"


class TestDataLinksValidatorBackwardCompatibility:
    """Test that imports work via scripts package."""

    def test_validator_importable_from_scripts_package(self, minimal_data_files):
        """Test that DataLinksValidator can be imported from scripts.validators."""
        from scripts.validators.links import DataLinksValidator as Import

        validator = Import(minimal_data_files)
        assert validator.__class__.__name__ == "DataLinksValidator"
        assert hasattr(validator, "validate_all")

    def test_validation_results_importable_from_scripts_package(self):
        """Test that ValidationResults can be imported from scripts.validators."""
        from scripts.validators.base import ValidationResults as Import

        results: Import = {
            "errors": [],
            "warnings": [],
            "fixes_needed": [],
            "correct": [],
        }
        assert isinstance(results, dict)
