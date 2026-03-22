"""GraphValidator - validates graph.json against all data files.

This module is organized into clear sections:
1. Constants and imports
2. Data loading and preparation
3. Global settings validation (lookup_method, price_source)
4. Links validation (product links, zones, weight_tiers)
5. Services validation
6. Dependencies validation
7. Units validation (weight, dimension, price, currency)
8. Circular dependencies validation
9. Main validation orchestrator
"""

import json
from pathlib import Path
from typing import Any

from scripts.data_files import (
    GRAPH_FILE,
    DEFAULT_PROVIDER,
    DIMENSIONS_FILE,
    GLOBAL_DIR,
    PROVIDERS_DIR,
    PRICES_FILE,
    PRODUCTS_FILE,
    SERVICES_FILE,
    WEIGHT_TIERS_FILE,
    ZONES_FILE,
    get_data_files,
    get_project_root,
)
from scripts.utils import load_json
from scripts.validators.base import ValidationResults
from scripts.validators.helpers import validate_unit_consistency

# ============================================================================
# Constants
# ============================================================================

# Business logic constants (not file paths)
EXPECTED_LOOKUP_ARRAY = "prices.product_prices"
EXPECTED_WEIGHT_UNIT = "g"
EXPECTED_DIMENSION_UNIT = "mm"
EXPECTED_PRICE_UNIT = "cents"
EXPECTED_CURRENCY = "EUR"


# ============================================================================
# GraphValidator Class
# ============================================================================


class GraphValidator:
    """Validates graph.json against all data files.

    The validator checks:
    - Lookup method configuration
    - Product links consistency
    - Zones and weight tiers validity
    - Services availability and pricing
    - Dependencies completeness
    - Unit consistency across files
    - Circular dependencies
    """

    def __init__(
        self,
        data_dir: Path | None = None,
        project_root: Path | None = None,
        provider: str | None = None,
    ) -> None:
        """Initialize validator with data directory or project root + provider.

        Args:
            data_dir: Path to directory containing all JSON files (legacy flat layout).
            project_root: Path to porto_data root (with global/, providers/).
            provider: Provider ID when using project_root (default: deutschepost).

        When data_dir is provided, uses legacy mode (all files in one dir).
        When project_root is provided, loads from global/ and providers/{provider}/.
        """
        if data_dir is not None:
            if not data_dir.exists():
                raise FileNotFoundError(f"Data directory does not exist: {data_dir}")
            if not data_dir.is_dir():
                raise ValueError(f"Path is not a directory: {data_dir}")
            self.data_dir = data_dir
            self.provider_dir = data_dir
            self.global_dir = data_dir
        else:
            root = project_root or get_project_root()
            prov = provider or DEFAULT_PROVIDER
            self.data_dir = root / PROVIDERS_DIR / prov
            self.provider_dir = root / PROVIDERS_DIR / prov
            self.global_dir = root / GLOBAL_DIR
            if not self.provider_dir.exists():
                raise FileNotFoundError(f"Provider directory does not exist: {self.provider_dir}")
        self.results: ValidationResults = {
            "errors": [],
            "warnings": [],
            "fixes_needed": [],
            "correct": [],
        }

        # Data files (loaded from JSON)
        self.graph: dict[str, Any] | None = None
        self.products: dict[str, Any] | None = None
        self.zones: dict[str, Any] | None = None
        self.weight_tiers: dict[str, Any] | None = None
        self.services: dict[str, Any] | None = None
        self.prices: dict[str, Any] | None = None
        self.dimensions: dict[str, Any] | None = None

        # Processed data structures (for quick lookup)
        self.product_dict: dict[str, dict[str, Any]] = {}
        self.zone_ids: dict[str, dict[str, Any]] = {}
        self.weight_tier_ids: set[str] = set()
        self.service_ids: dict[str, dict[str, Any]] = {}
        self.services_by_id: dict[str, dict[str, Any]] = {}
        self.product_prices: list[dict[str, Any]] = []
        self.service_prices: list[dict[str, Any]] = []
        self.all_data_files: set[str] = set()

    # ========================================================================
    # Data Loading
    # ========================================================================

    def load_data(self) -> None:
        """Load all required JSON files and build lookup structures."""
        if self.graph is not None:
            return  # Already loaded

        try:
            self.graph = load_json(self.provider_dir / GRAPH_FILE)
            self.products = load_json(self.provider_dir / PRODUCTS_FILE)
            self.zones = load_json(self.provider_dir / ZONES_FILE)
            self.weight_tiers = load_json(self.provider_dir / WEIGHT_TIERS_FILE)
            self.services = load_json(self.provider_dir / SERVICES_FILE)
            self.prices = load_json(self.provider_dir / PRICES_FILE)
            self.dimensions = load_json(self.global_dir / DIMENSIONS_FILE)
        except FileNotFoundError as e:
            self.results["errors"].append(f"Missing file: {str(e)}")
            return
        except json.JSONDecodeError as e:
            self.results["errors"].append(f"Invalid JSON: {str(e)}")
            return

        # Build lookup structures for efficient validation
        self._build_lookup_structures()

    def _build_lookup_structures(self) -> None:
        """Build lookup dictionaries and sets from loaded data."""
        if self.products is None or self.zones is None:
            return

        self.product_dict = {p["id"]: p for p in self.products.get("products", [])}
        self.zone_ids = {z["id"]: z for z in self.zones.get("zones", [])}
        self.weight_tier_ids = (
            set(self.weight_tiers.get("weight_tiers", {}).keys()) if self.weight_tiers else set()
        )
        self.service_ids = (
            {s["id"]: s for s in self.services.get("services", [])} if self.services else {}
        )
        self.services_by_id = (
            {s["id"]: s for s in self.services.get("services", [])} if self.services else {}
        )
        self.product_prices = (
            self.prices.get("prices", {}).get("product_prices", []) if self.prices else []
        )
        self.service_prices = (
            self.prices.get("prices", {}).get("service_prices", []) if self.prices else []
        )
        self.all_data_files = get_data_files()

    def _service_refs_set(self) -> set[str]:
        """Provider `id` and unified `porto_id` strings that may appear in graph/prices."""
        if not self.services:
            return set()
        out: set[str] = set()
        for s in self.services.get("services", []):
            if s.get("id"):
                out.add(str(s["id"]))
            if s.get("porto_id"):
                out.add(str(s["porto_id"]))
        return out

    def _get_service_by_ref(self, ref: str) -> dict[str, Any] | None:
        """Resolve a service row by provider `id` or `porto_id`."""
        if not self.services or not ref:
            return None
        for s in self.services.get("services", []):
            if s.get("id") == ref or s.get("porto_id") == ref:
                return s
        return None

    # ========================================================================
    # Global Settings Validation
    # ========================================================================

    def validate_lookup_method(self) -> None:
        """Validate lookup_method configuration in global_settings."""
        if self.graph is None:
            return

        global_settings = self.graph.get("global_settings", {})
        lookup_method = global_settings.get("lookup_method", {})
        price_source = global_settings.get("price_source", "")

        # Validate lookup_method.file
        self._validate_file_reference(
            lookup_method.get("file", ""),
            PRICES_FILE,
            "lookup_method.file",
            ["global_settings", "lookup_method", "file"],
        )

        # Validate price_source
        self._validate_file_reference(
            price_source,
            PRICES_FILE,
            "price_source",
            ["global_settings", "price_source"],
        )

        # Validate lookup_method.array path
        self._validate_lookup_array(lookup_method.get("array", ""))

        # Validate lookup_method.match keys
        self._validate_lookup_match_keys(lookup_method.get("match", {}))

    def _validate_file_reference(
        self, actual: str, expected: str, field_name: str, path_parts: list[str]
    ) -> None:
        """Validate that a file reference matches expected value.

        Args:
            actual: Actual file name from data.
            expected: Expected file name.
            field_name: Name of the field being validated.
            path_parts: Path parts for error context.
        """
        if actual == expected:
            if expected in self.all_data_files:
                self.results["correct"].append(f"{field_name} '{expected}' matches actual file")
            else:
                self.results["errors"].append(
                    f"{field_name} references '{expected}' but file doesn't exist. "
                    f"Found in: {GRAPH_FILE} -> {' -> '.join(path_parts)}"
                )
        else:
            self.results["errors"].append(
                f"{field_name} '{actual}' should be '{expected}'. "
                f"Found in: {GRAPH_FILE} -> {' -> '.join(path_parts)}"
            )

    def _validate_lookup_array(self, lookup_array: str) -> None:
        """Validate lookup_method.array path matches actual structure."""
        if lookup_array == EXPECTED_LOOKUP_ARRAY:
            if (
                self.prices
                and "prices" in self.prices
                and "product_prices" in self.prices["prices"]
            ):
                self.results["correct"].append(
                    f"lookup_method.array '{EXPECTED_LOOKUP_ARRAY}' matches actual structure"
                )
            else:
                self.results["errors"].append(
                    f"Lookup method references '{EXPECTED_LOOKUP_ARRAY}' but structure doesn't match. "
                    f"Found in: {GRAPH_FILE} -> global_settings -> lookup_method -> array"
                )
        else:
            self.results["warnings"].append(
                f"Lookup method array path '{lookup_array}' - verify this matches actual structure. "
                f"Expected: '{EXPECTED_LOOKUP_ARRAY}'. "
                f"Found in: {GRAPH_FILE} -> global_settings -> lookup_method -> array"
            )

    def _validate_lookup_match_keys(self, lookup_match: dict[str, Any]) -> None:
        """Validate lookup_method.match keys exist in price entries."""
        if not self.product_prices:
            self.results["warnings"].append(
                "No product prices found to validate lookup_method.match keys"
            )
            return

        sample_price_keys = set(self.product_prices[0].keys())
        expected_match_keys = set(lookup_match.keys())
        match_keys_to_check = {k for k in expected_match_keys if k != "description"}

        missing_keys = match_keys_to_check - sample_price_keys
        if missing_keys:
            self.results["errors"].append(
                f"lookup_method.match keys {sorted(missing_keys)} do not exist in price entries. "
                f"Available keys: {sorted(sample_price_keys)}. "
                f"Found in: {GRAPH_FILE} -> global_settings -> lookup_method -> match"
            )
        else:
            self.results["correct"].append(
                f"lookup_method.match keys {sorted(match_keys_to_check)} exist in price entries"
            )

    # ========================================================================
    # Links Validation
    # ========================================================================

    def validate_links(self) -> None:
        """Validate links section - product links, zones, and weight_tiers."""
        if self.graph is None:
            return

        links = self.graph.get("links", {})
        for product_id, link_data in links.items():
            self._validate_product_link(product_id, link_data)

    def _validate_product_link(self, product_id: str, link_data: dict[str, Any]) -> None:
        """Validate a single product link.

        Args:
            product_id: Product ID from links.
            link_data: Link data for this product.
        """
        # Check if product exists
        if product_id not in self.product_dict:
            self.results["errors"].append(
                f"Product '{product_id}' in links does not exist in {PRODUCTS_FILE}. "
                f"Found in: {GRAPH_FILE} -> links -> {product_id}"
            )
            return

        product = self.product_dict[product_id]
        link_zones = set(link_data.get("zones", []))
        link_weight_tiers = set(link_data.get("weight_tiers", []))
        product_zones = set(product.get("supported_zones", []))
        product_weight_tier = product.get("weight_tier")

        # Validate zones
        self._validate_product_zones(product_id, link_zones, product_zones)

        # Validate weight_tiers
        self._validate_product_weight_tiers(product_id, link_weight_tiers, product_weight_tier)

        # Check price coverage
        self._validate_price_coverage(product_id, link_zones, link_weight_tiers)

    def _validate_product_zones(
        self, product_id: str, link_zones: set[str], product_zones: set[str]
    ) -> None:
        """Validate zones for a product."""
        # Check zone existence
        for zone in link_zones:
            if zone not in self.zone_ids:
                self.results["errors"].append(
                    f"Zone '{zone}' for product '{product_id}' does not exist in {ZONES_FILE}. "
                    f"Found in: {GRAPH_FILE} -> links -> {product_id} -> zones"
                )

        # Check zone consistency
        if link_zones == product_zones:
            self.results["correct"].append(
                f"Product '{product_id}': zones match ({sorted(link_zones)})"
            )
        else:
            self.results["fixes_needed"].append(
                f"Product '{product_id}': zones mismatch - links: {sorted(link_zones)}, "
                f"product: {sorted(product_zones)}"
            )

    def _validate_product_weight_tiers(
        self, product_id: str, link_weight_tiers: set[str], product_weight_tier: str | None
    ) -> None:
        """Validate weight_tiers for a product."""
        # Check weight_tier existence
        for wt in link_weight_tiers:
            if wt not in self.weight_tier_ids:
                self.results["errors"].append(
                    f"Weight tier '{wt}' for product '{product_id}' does not exist in {WEIGHT_TIERS_FILE}. "
                    f"Found in: {GRAPH_FILE} -> links -> {product_id} -> weight_tiers"
                )

        # Find all weight tiers that have prices for this product
        price_weight_tiers = {
            p["weight_tier"] for p in self.product_prices if p.get("product_id") == product_id
        }

        # Check if product's weight_tier is in links
        if product_weight_tier and product_weight_tier in link_weight_tiers:
            self.results["correct"].append(
                f"Product '{product_id}': weight_tier '{product_weight_tier}' is in links"
            )
        elif product_weight_tier:
            self.results["fixes_needed"].append(
                f"Product '{product_id}': weight_tier '{product_weight_tier}' from product "
                f"not in links {sorted(link_weight_tiers)}"
            )

        # Check if all price weight_tiers are in links
        missing_tiers = price_weight_tiers - link_weight_tiers
        if missing_tiers:
            self.results["fixes_needed"].append(
                f"Product '{product_id}': prices exist for weight_tiers {sorted(missing_tiers)} but not in links"
            )
        elif price_weight_tiers == link_weight_tiers:
            self.results["correct"].append(
                f"Product '{product_id}': all price weight_tiers match links ({sorted(price_weight_tiers)})"
            )

    def _validate_price_coverage(
        self, product_id: str, link_zones: set[str], link_weight_tiers: set[str]
    ) -> None:
        """Check if prices exist for all zone+weight_tier combinations."""
        for zone in link_zones:
            for weight_tier in link_weight_tiers:
                matching_price = any(
                    p.get("product_id") == product_id
                    and p.get("zone") == zone
                    and p.get("weight_tier") == weight_tier
                    for p in self.product_prices
                )
                if not matching_price:
                    self.results["warnings"].append(
                        f"No price found for product '{product_id}', zone '{zone}', weight_tier '{weight_tier}'"
                    )

    def validate_products_in_links(self) -> None:
        """Check for products not in links."""
        if self.graph is None:
            return

        links = self.graph.get("links", {})
        products_in_data = set(self.product_dict.keys())
        products_in_links = set(links.keys())
        missing_products = products_in_data - products_in_links

        if missing_products:
            self.results["fixes_needed"].append(
                f"Products in products.json but not in links: {sorted(missing_products)}"
            )
        else:
            self.results["correct"].append("All products are in links")

    def validate_zones_and_weight_tiers(self) -> None:
        """Verify all zones and weight_tiers in links exist."""
        if self.graph is None:
            return

        links = self.graph.get("links", {})

        # Collect all zones and weight_tiers from links
        all_link_zones = set()
        all_link_weight_tiers = set()
        for link_data in links.values():
            all_link_zones.update(link_data.get("zones", []))
            all_link_weight_tiers.update(link_data.get("weight_tiers", []))

        # Validate zones
        invalid_zones = all_link_zones - set(self.zone_ids.keys())
        if not invalid_zones:
            self.results["correct"].append("All zones in links are valid")

        # Validate weight_tiers
        invalid_weight_tiers = all_link_weight_tiers - self.weight_tier_ids
        if not invalid_weight_tiers:
            self.results["correct"].append("All weight_tiers in links are valid")

    # ========================================================================
    # Services Validation
    # ========================================================================

    def validate_available_services(self) -> None:
        """Validate available_services and service-price consistency."""
        if self.graph is None:
            return

        available_services = self.graph.get("global_settings", {}).get(
            "available_services", []
        )

        # Validate service existence
        valid_refs = self._service_refs_set()
        for sp in self.service_prices:
            sid = sp.get("service_id")
            if not sid:
                continue
            if str(sid) not in valid_refs:
                self.results["errors"].append(
                    f"Service '{sid}' in service_prices does not exist in {SERVICES_FILE} "
                    f"(by id or porto_id). Found in: {PRICES_FILE} -> prices -> service_prices"
                )

        for service_id in available_services:
            if service_id not in valid_refs:
                self.results["errors"].append(
                    f"Service '{service_id}' in available_services does not exist in {SERVICES_FILE}. "
                    f"Found in: {GRAPH_FILE} -> global_settings -> available_services"
                )

        # Check if all services have prices
        service_price_ids = {sp.get("service_id") for sp in self.service_prices}
        for service_id in available_services:
            if service_id not in service_price_ids:
                self.results["warnings"].append(
                    f"Service '{service_id}' is listed as available but has no price in prices.json"
                )

        # Validate service-price effective date consistency
        self._validate_service_price_consistency()

    def _validate_service_price_consistency(self) -> None:
        """Validate that service and price effective_to dates match."""
        for price_entry in self.service_prices:
            service_id = price_entry.get("service_id")
            if not service_id:
                continue

            # Find effective_to from price entries
            price_entries = price_entry.get("price", [])
            price_effective_to = None
            for price_item in price_entries:
                effective_to = price_item.get("effective_to")
                if effective_to is not None:
                    price_effective_to = effective_to
                    break

            # If price has effective_to, service must also have it
            if price_effective_to is not None:
                service = self._get_service_by_ref(str(service_id))
                if not service:
                    self.results["errors"].append(
                        f"Service '{service_id}' has prices but service not found in services.json"
                    )
                    continue

                service_effective_to = service.get("effective_to")

                if service_effective_to is None:
                    self.results["errors"].append(
                        f"Service '{service_id}' has prices with effective_to='{price_effective_to}' "
                        f"but service does not have effective_to set. Service must be marked as discontinued "
                        f"when prices are discontinued. "
                        f"Price found in: {PRICES_FILE} -> prices -> service_prices. "
                        f"Service found in: {SERVICES_FILE} -> services"
                    )
                elif service_effective_to != price_effective_to:
                    self.results["errors"].append(
                        f"Service '{service_id}' has price effective_to='{price_effective_to}' "
                        f"but service effective_to='{service_effective_to}'. Dates must match. "
                        f"Price found in: {PRICES_FILE} -> prices -> service_prices. "
                        f"Service found in: {SERVICES_FILE} -> services"
                    )

    def validate_execution_semantics(self) -> None:
        """Validate mark_type / tracking_mode and optional tracking service linkage."""
        if self.products is None or self.services is None:
            return

        available_services = (
            (self.graph or {}).get("global_settings", {}).get("available_services") or []
        )
        if not isinstance(available_services, list):
            available_services = []

        for product_id, product in self.product_dict.items():
            mark_type = product.get("mark_type")
            tracking_mode = product.get("tracking_mode")
            if mark_type is None or tracking_mode is None:
                self.results["errors"].append(
                    f"Product '{product_id}' must define mark_type and tracking_mode "
                    f"({PRODUCTS_FILE})"
                )
                continue

            if mark_type == "label" and tracking_mode == "none":
                self.results["errors"].append(
                    f"Product '{product_id}': invalid combination label + tracking_mode none "
                    f"(use optional or included)"
                )

            if tracking_mode != "optional":
                continue

            p_zones = set(product.get("supported_zones") or [])

            def _service_covers_product(svc: dict[str, Any]) -> bool:
                sz = svc.get("supported_zones")
                if not sz:
                    return True
                return bool(p_zones & set(sz))

            ok = False
            for sid in available_services:
                svc = self._get_service_by_ref(str(sid))
                if not svc or not svc.get("enables_tracking"):
                    continue
                if _service_covers_product(svc):
                    ok = True
                    break

            if not ok:
                for svc in self.services_by_id.values():
                    if not svc.get("enables_tracking"):
                        continue
                    if _service_covers_product(svc):
                        ok = True
                        break

            if not ok:
                self.results["errors"].append(
                    f"Product '{product_id}' has tracking_mode optional but no service with "
                    f"enables_tracking covers its zones in {SERVICES_FILE} / available_services "
                    f"({GRAPH_FILE})"
                )

    # ========================================================================
    # Dependencies Validation
    # ========================================================================

    def validate_dependencies(self) -> None:
        """Validate dependencies section."""
        if self.graph is None:
            return

        dependencies = self.graph.get("dependencies", {})

        # Check if all data files are covered in dependencies
        expected_data_files = self.all_data_files - {GRAPH_FILE}
        files_in_dependencies = {dep_data.get("file") for dep_data in dependencies.values()}
        missing_in_dependencies = expected_data_files - files_in_dependencies

        if missing_in_dependencies:
            self.results["fixes_needed"].append(
                f"Data files not in dependencies section: {sorted(missing_in_dependencies)}"
            )
        else:
            self.results["correct"].append("All data files are covered in dependencies section")

        # Validate individual dependency entries
        for dep_name, dep_data in dependencies.items():
            dep_file = dep_data.get("file")
            if dep_file not in self.all_data_files:
                self.results["warnings"].append(
                    f"Dependency file '{dep_file}' is not a known data file"
                )

            depends_on = dep_data.get("depends_on", [])
            for dep_file_name in depends_on:
                if dep_file_name not in self.all_data_files:
                    self.results["warnings"].append(
                        f"Dependency '{dep_file_name}' in '{dep_name}' is not a known data file"
                    )

    # ========================================================================
    # Units Validation
    # ========================================================================

    def validate_units(self) -> None:
        """Validate all unit values consistency."""
        self.validate_weight_units()
        self.validate_dimension_units()
        self.validate_price_units()
        self.validate_currency_units()

    def validate_weight_units(self) -> None:
        """Validate weight unit consistency."""
        if not all([self.graph, self.products, self.weight_tiers]):
            return

        assert self.graph is not None
        assert self.products is not None
        assert self.weight_tiers is not None

        data_links_weight = self.graph.get("unit", {}).get("weight")
        products_weight = self.products.get("unit", {}).get("weight")
        weight_tiers_weight = self.weight_tiers.get("unit", {}).get("weight")

        validate_unit_consistency(
            unit_name="weight",
            data_links_value=data_links_weight,
            expected_value=EXPECTED_WEIGHT_UNIT,
            file_names=[GRAPH_FILE, PRODUCTS_FILE, WEIGHT_TIERS_FILE],
            results=self.results,
            other_values=[products_weight, weight_tiers_weight],
        )

    def validate_dimension_units(self) -> None:
        """Validate dimension unit consistency (graph + global dimensions only; products.json has no linear dimension unit)."""
        if not all([self.graph, self.dimensions]):
            return

        assert self.graph is not None
        assert self.dimensions is not None

        data_links_dimension = self.graph.get("unit", {}).get("dimension")
        dimensions_dimension = self.dimensions.get("unit", {}).get("dimension")

        validate_unit_consistency(
            unit_name="dimension",
            data_links_value=data_links_dimension,
            expected_value=EXPECTED_DIMENSION_UNIT,
            file_names=[GRAPH_FILE, DIMENSIONS_FILE],
            results=self.results,
            other_values=[dimensions_dimension],
        )

    def validate_price_units(self) -> None:
        """Validate price unit consistency."""
        if not all([self.graph, self.prices]):
            return

        assert self.graph is not None
        assert self.prices is not None

        data_links_price = self.graph.get("unit", {}).get("price")
        prices_price = self.prices.get("unit", {}).get("price")

        validate_unit_consistency(
            unit_name="price",
            data_links_value=data_links_price,
            expected_value=EXPECTED_PRICE_UNIT,
            file_names=[GRAPH_FILE, PRICES_FILE],
            results=self.results,
            other_values=[prices_price],
        )

    def validate_currency_units(self) -> None:
        """Validate currency unit consistency."""
        if not all([self.graph, self.prices]):
            return

        assert self.graph is not None
        assert self.prices is not None

        data_links_currency = self.graph.get("unit", {}).get("currency")
        prices_currency = self.prices.get("unit", {}).get("currency")

        validate_unit_consistency(
            unit_name="currency",
            data_links_value=data_links_currency,
            expected_value=EXPECTED_CURRENCY,
            file_names=[GRAPH_FILE, PRICES_FILE],
            results=self.results,
            other_values=[prices_currency],
        )

    # ========================================================================
    # Circular Dependencies Validation
    # ========================================================================

    def validate_circular_dependencies(self) -> None:
        """Check for circular dependencies."""
        if self.graph is None:
            return

        dependencies = self.graph.get("dependencies", {})
        dep_graph: dict[str, set[str]] = {}

        for _dep_name, dep_data in dependencies.items():
            dep_file = dep_data.get("file", "").replace(".json", "")
            depends_on = {d.replace(".json", "") for d in dep_data.get("depends_on", [])}
            dep_graph[dep_file] = depends_on

        # Simple circular dependency check (products -> prices -> products)
        if "products" in dep_graph.get("prices", set()) and "prices" in dep_graph.get(
            "products", set()
        ):
            self.results["warnings"].append(
                "Circular dependency detected: products depends on prices, and prices depends on products. "
                "This may be intentional but should be reviewed."
            )

    # ========================================================================
    # Main Validation Orchestrator
    # ========================================================================

    def validate_all(self) -> ValidationResults:
        """Run all validations in logical order.

        Returns:
            ValidationResults dictionary with errors, warnings, fixes_needed, and correct items.
        """
        self.load_data()

        # If loading failed, return early
        if self.results["errors"]:
            return self.results

        # Run all validation methods in logical groups
        self.validate_lookup_method()
        self.validate_links()
        self.validate_products_in_links()
        self.validate_zones_and_weight_tiers()
        self.validate_available_services()
        self.validate_execution_semantics()
        self.validate_dependencies()
        self.validate_units()
        self.validate_circular_dependencies()

        return self.results


# ============================================================================
# Standalone validation function (used by CLI)
# ============================================================================


def validate_graph(
    data_dir: Path | None = None,
    project_root: Path | None = None,
    provider: str | None = None,
    analyze: bool = False,
) -> int:
    """Validate graph.json and print results.

    Args:
        data_dir: Path to data directory (legacy flat layout). If None, uses project_root + provider.
        project_root: Path to porto_data root (with global/, providers/). Defaults to get_project_root().
        provider: Provider ID (default: deutschepost).
        analyze: If True, show detailed analysis. If False, CI/CD friendly output.

    Returns:
        Exit code: 0 if validation passes, 1 otherwise.
    """
    prov = provider or DEFAULT_PROVIDER
    validator = GraphValidator(data_dir=data_dir, project_root=project_root, provider=provider)
    results = validator.validate_all()

    if analyze:
        return _print_analyze_mode(results, provider_label=prov)
    else:
        return _print_validate_mode(results, provider_label=prov)


def _print_validate_mode(results: ValidationResults, provider_label: str = "") -> int:
    """Print results in validate mode (CI/CD friendly)."""
    label = f" ({provider_label})" if provider_label else ""
    print(f"Validating graph.json against data files{label}...\n")

    has_errors = len(results["errors"]) > 0

    if results["errors"]:
        for error in results["errors"]:
            print(f"❌ ERROR: {error}")
        print()

    if results["fixes_needed"]:
        for fix in results["fixes_needed"]:
            print(f"🔧 FIX NEEDED: {fix}")
        print()

    if results["warnings"]:
        for warning in results["warnings"]:
            print(f"⚠️  WARNING: {warning}")
        print()

    if not has_errors:
        print("✅ All validations passed! graph.json is consistent with data files.")
        return 0
    else:
        print("❌ ERROR: Validation failed. Please fix the errors above.")
        return 1


def _print_analyze_mode(results: ValidationResults, provider_label: str = "") -> int:
    """Print results in analyze mode (detailed report)."""
    print("=" * 70)
    suffix = f" — {provider_label}" if provider_label else ""
    print(f"COMPREHENSIVE GRAPH.JSON ANALYSIS{suffix}")
    print("=" * 70)
    print()

    if results["correct"]:
        print("✅ CORRECT:")
        for item in results["correct"]:
            print(f"   ✅ {item}")
        print()

    if results["fixes_needed"]:
        print("🔧 FIXES NEEDED:")
        for item in results["fixes_needed"]:
            print(f"   🔧 {item}")
        print()

    if results["warnings"]:
        print("⚠️  WARNINGS:")
        for item in results["warnings"]:
            print(f"   ⚠️  {item}")
        print()

    if results["errors"]:
        print("❌ ERRORS:")
        for item in results["errors"]:
            print(f"   ❌ {item}")
        print()

    # Summary
    total_issues = len(results["errors"]) + len(results["fixes_needed"]) + len(results["warnings"])
    if total_issues == 0:
        print("🎉 All checks passed! graph.json is correct.")
        return 0
    else:
        print(
            f"📊 Summary: {len(results['errors'])} errors, "
            f"{len(results['fixes_needed'])} fixes needed, "
            f"{len(results['warnings'])} warnings"
        )
        return 1 if results["errors"] else 0


# Backward-compatible names (deprecated)
validate_resolution_graph = validate_graph
ResolutionGraphValidator = GraphValidator
