"""GraphValidator - validates graph.json against all data files.

This module is organized into clear sections:
1. Constants and imports
2. Data loading and preparation
3. Global settings validation (price_lookup)
4. ``graph.edges`` validation (product × zones × weight_tiers in graph.json)
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
    DEFAULT_PROVIDER,
    ENVELOPES_FILE,
    GRAPH_FILE,
    LAYOUTS_FILE,
    MARKS_FILE,
    POLICY_MAPPINGS_KEY,
    PRODUCT_PRICES_FILE,
    PRODUCTS_FILE,
    PROVIDERS_DIR,
    SERVICE_PRICES_FILE,
    SERVICES_FILE,
    WEIGHTS_FILE,
    ZONES_FILE,
    get_data_file_path,
    get_graph_dependency_file_refs,
    get_project_root,
)
from scripts.utils import load_json
from scripts.validators.base import ValidationResults
from scripts.validators.helpers import validate_unit_consistency

# ============================================================================
# Constants
# ============================================================================

# Business logic constants (not file paths)
EXPECTED_PRODUCT_PRICES_ARRAY = "product_prices"
EXPECTED_SERVICE_PRICES_ARRAY = "service_prices"
EXPECTED_WEIGHT_UNIT = "g"
EXPECTED_DIMENSION_UNIT = "mm"
EXPECTED_PRICE_UNIT = "cents"

# provider_rules.json — keep in sync with schemas/rules.schema.json
PROVIDER_RULE_KIND_METRIC_BAND_ATTACH = "metric_band_attach_service"
PROVIDER_RULE_METRIC_THICKNESS = "thickness"
EXPECTED_CURRENCY = "EUR"

_RECT_KEYS = ("x", "y", "width", "height")


def _envelope_rect_complete(r: Any) -> bool:
    """True if r is a dict with integer x, y, width, height."""
    if not isinstance(r, dict):
        return False
    return all(isinstance(r.get(k), int) for k in _RECT_KEYS)


def _envelope_rect_equal(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return all(a.get(k) == b.get(k) for k in _RECT_KEYS)


def _envelope_validation_views(env: dict[str, Any]) -> dict[str, Any]:
    """Nested layout.* (print/stamp/address/window) or legacy top-level areas + window flags."""
    rend = env.get("layout")
    if isinstance(rend, dict) and isinstance(rend.get("print_area"), dict):
        win = rend.get("window") or {}
        sup = win.get("supported")
        wa = win.get("area") if sup is True else None
        return {
            "addr": rend.get("address_area"),
            "pa": rend.get("print_area"),
            "wa": wa,
            "has_w": _envelope_rect_complete(wa),
            "no_window": sup is False,
            "force_window": sup is True,
        }
    wa_legacy = env.get("window_area")
    return {
        "addr": env.get("address_area"),
        "pa": env.get("print_area"),
        "wa": wa_legacy,
        "has_w": _envelope_rect_complete(wa_legacy),
        "no_window": env.get("supports_window") is False,
        "force_window": env.get("window_supported") is True,
    }


# ============================================================================
# GraphValidator Class
# ============================================================================


class GraphValidator:
    """Validates graph.json against all data files.

    The validator checks:
    - Lookup method configuration
    - ``edges`` object consistency (per product)
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
            data_dir: Path to directory containing all JSON files (single-directory layout).
            project_root: Path to porto_data root (with policy/, mails/, providers/).
            provider: Provider ID when using project_root (default: deutschepost).

        When data_dir is provided, all entity files are read from that directory.
        When project_root is provided, loads shared bundle files and providers/{provider}/.
        """
        if data_dir is not None:
            if not data_dir.exists():
                raise FileNotFoundError(f"Data directory does not exist: {data_dir}")
            if not data_dir.is_dir():
                raise ValueError(f"Path is not a directory: {data_dir}")
            self.data_dir = data_dir
            self.provider_dir = data_dir
            self.shared_bundle_subdir = data_dir
            self._bundle_root = data_dir
        else:
            root = project_root or get_project_root()
            prov = provider or DEFAULT_PROVIDER
            self.data_dir = root / PROVIDERS_DIR / prov
            self.provider_dir = root / PROVIDERS_DIR / prov
            # porto_data/policy/ — bundle subtree; used for flat-layout detection vs bundle root
            self.shared_bundle_subdir = root / POLICY_MAPPINGS_KEY
            self._bundle_root = root
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
        self.product_prices_doc: dict[str, Any] | None = None
        self.service_prices_doc: dict[str, Any] | None = None
        self.provider_rules_doc: dict[str, Any] | None = None
        self.envelopes: dict[str, Any] | None = None
        self.envelope_layouts: dict[str, Any] | None = None
        self.marks: dict[str, Any] | None = None

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
            self.weight_tiers = load_json(self.provider_dir / WEIGHTS_FILE)
            self.services = load_json(self.provider_dir / SERVICES_FILE)
            prices_dir = self.provider_dir / "prices"
            self.product_prices_doc = load_json(prices_dir / PRODUCT_PRICES_FILE)
            self.service_prices_doc = load_json(prices_dir / SERVICE_PRICES_FILE)
            if self.shared_bundle_subdir == self._bundle_root:
                fmt_path = self.data_dir / ENVELOPES_FILE
                lay_path = self.data_dir / LAYOUTS_FILE
            else:
                fmt_path = get_data_file_path("envelopes", project_root=self._bundle_root)
                lay_path = get_data_file_path("layouts", project_root=self._bundle_root)
            self.envelopes = load_json(fmt_path)
            self.envelope_layouts = load_json(lay_path)
            self.marks = load_json(self.provider_dir / MARKS_FILE)
            rules_path = self.provider_dir / "rules.json"
            if rules_path.is_file():
                self.provider_rules_doc = load_json(rules_path)
            else:
                self.provider_rules_doc = None
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
            set(self.weight_tiers.get("weights", {}).keys()) if self.weight_tiers else set()
        )
        self.service_ids = (
            {s["id"]: s for s in self.services.get("services", [])} if self.services else {}
        )
        self.services_by_id = (
            {s["id"]: s for s in self.services.get("services", [])} if self.services else {}
        )
        self.product_prices = (
            self.product_prices_doc.get("product_prices", []) if self.product_prices_doc else []
        )
        self.service_prices = (
            self.service_prices_doc.get("service_prices", []) if self.service_prices_doc else []
        )
        if self.shared_bundle_subdir == self._bundle_root:
            self.all_data_files = {
                p.relative_to(self.data_dir).as_posix() for p in self.data_dir.rglob("*.json")
            }
        else:
            self.all_data_files = get_graph_dependency_file_refs(self.provider_dir.name)

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
            if isinstance(s, dict) and (s.get("id") == ref or s.get("porto_id") == ref):
                return s
        return None

    # ========================================================================
    # Global Settings Validation
    # ========================================================================

    def validate_lookup_method(self) -> None:
        """Validate price_lookup configuration in global_settings."""
        if self.graph is None:
            return

        global_settings = self.graph.get("global_settings", {})
        price_lookup = global_settings.get("price_lookup", {})
        if not isinstance(price_lookup, dict):
            return

        pp = price_lookup.get("product_prices", {})
        sp = price_lookup.get("service_prices", {})

        if self.shared_bundle_subdir == self._bundle_root:
            expected_pp = f"prices/{PRODUCT_PRICES_FILE}"
            expected_sp = f"prices/{SERVICE_PRICES_FILE}"
        else:
            prov = self.provider_dir.name
            root = self._bundle_root
            pbase = root / PROVIDERS_DIR / prov
            expected_pp = (
                get_data_file_path("product_prices", prov, project_root=root)
                .relative_to(pbase)
                .as_posix()
            )
            expected_sp = (
                get_data_file_path("service_prices", prov, project_root=root)
                .relative_to(pbase)
                .as_posix()
            )

        self._validate_file_reference(
            pp.get("file", "") if isinstance(pp, dict) else "",
            expected_pp,
            "price_lookup.product_prices.file",
            ["global_settings", "price_lookup", "product_prices", "file"],
        )
        self._validate_file_reference(
            sp.get("file", "") if isinstance(sp, dict) else "",
            expected_sp,
            "price_lookup.service_prices.file",
            ["global_settings", "price_lookup", "service_prices", "file"],
        )

        if isinstance(pp, dict):
            self._validate_lookup_array(
                pp.get("array", ""),
                EXPECTED_PRODUCT_PRICES_ARRAY,
                "product_prices",
                self.product_prices_doc,
                "product_prices",
            )
            self._validate_lookup_match_keys(pp.get("match", {}), for_product_prices=True)

        if isinstance(sp, dict):
            self._validate_lookup_array(
                sp.get("array", ""),
                EXPECTED_SERVICE_PRICES_ARRAY,
                "service_prices",
                self.service_prices_doc,
                "service_prices",
            )
            self._validate_lookup_match_keys(sp.get("match", {}), for_product_prices=False)

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

    def _validate_lookup_array(
        self,
        lookup_array: str,
        expected: str,
        label: str,
        doc: dict[str, Any] | None,
        top_key: str,
    ) -> None:
        """Validate price_lookup.*.array matches actual JSON top-level key."""
        path_hint = f"{GRAPH_FILE} -> global_settings -> price_lookup -> {label} -> array"
        if lookup_array == expected:
            if doc and top_key in doc and isinstance(doc.get(top_key), list):
                self.results["correct"].append(
                    f"price_lookup.{label}.array '{expected}' matches actual structure"
                )
            else:
                self.results["errors"].append(
                    f"Lookup references '{expected}' but structure doesn't match. Found in: {path_hint}"
                )
        else:
            self.results["warnings"].append(
                f"price_lookup.{label}.array path {lookup_array!r} — expected {expected!r}. {path_hint}"
            )

    def _validate_lookup_match_keys(
        self, lookup_match: dict[str, Any], *, for_product_prices: bool
    ) -> None:
        """Validate price_lookup.*.match keys exist in price rows."""
        path = (
            f"{GRAPH_FILE} -> global_settings -> price_lookup -> "
            f"{'product_prices' if for_product_prices else 'service_prices'} -> match"
        )
        if for_product_prices:
            if not self.product_prices:
                self.results["warnings"].append(
                    "No product prices found to validate price_lookup.product_prices.match keys"
                )
                return
            sample_keys = set(self.product_prices[0].keys())
        else:
            if not self.service_prices:
                self.results["warnings"].append(
                    "No service prices found to validate price_lookup.service_prices.match keys"
                )
                return
            sample_keys = set(self.service_prices[0].keys())

        expected_match_keys = set(lookup_match.keys())
        match_keys_to_check = {k for k in expected_match_keys if k != "description"}
        missing_keys = match_keys_to_check - sample_keys
        if missing_keys:
            self.results["errors"].append(
                f"price_lookup match keys {sorted(missing_keys)} do not exist in entries. "
                f"Available keys: {sorted(sample_keys)}. Found in: {path}"
            )
        else:
            self.results["correct"].append(
                f"price_lookup match keys {sorted(match_keys_to_check)} exist in entries ({path})"
            )

    # ========================================================================
    # Edges validation (graph.edges)
    # ========================================================================

    def validate_edges(self) -> None:
        """Validate graph.edges: per-product zones and weight_tiers."""
        if self.graph is None:
            return

        edges = self.graph.get("edges", {})
        for product_id, edge_data in edges.items():
            self._validate_product_edge(product_id, edge_data)

    def _validate_product_edge(self, product_id: str, edge_data: dict[str, Any]) -> None:
        """Validate a single product edge (zones + weight_tiers).

        Args:
            product_id: Product id from graph.edges.
            edge_data: zones and weight_tiers for this product.
        """
        # Check if product exists
        if product_id not in self.product_dict:
            self.results["errors"].append(
                f"Product '{product_id}' in edges does not exist in {PRODUCTS_FILE}. "
                f"Found in: {GRAPH_FILE} -> edges -> {product_id}"
            )
            return

        product = self.product_dict[product_id]
        link_zones = set(edge_data.get("zones", []))
        link_weight_tiers = set(edge_data.get("weight_tiers", []))
        product_zones = set(product.get("zones", []))
        product_weight_tier = product.get("weight_tier")

        # Validate zones
        self._validate_product_zones(product_id, link_zones, product_zones)

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
                    f"Found in: {GRAPH_FILE} -> edges -> {product_id} -> zones"
                )

        # Check zone consistency
        if link_zones == product_zones:
            self.results["correct"].append(
                f"Product '{product_id}': zones match ({sorted(link_zones)})"
            )
        else:
            self.results["fixes_needed"].append(
                f"Product '{product_id}': zones mismatch - edges: {sorted(link_zones)}, "
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
                    f"Weight tier '{wt}' for product '{product_id}' does not exist in {WEIGHTS_FILE}. "
                    f"Found in: {GRAPH_FILE} -> edges -> {product_id} -> weight_tiers"
                )

        # Find all weight tiers that have prices for this product
        price_weight_tiers = {
            p["weight_tier"] for p in self.product_prices if p.get("product_id") == product_id
        }

        if product_weight_tier and product_weight_tier in link_weight_tiers:
            self.results["correct"].append(
                f"Product '{product_id}': weight_tier '{product_weight_tier}' is in edges"
            )
        elif product_weight_tier:
            self.results["fixes_needed"].append(
                f"Product '{product_id}': weight_tier '{product_weight_tier}' from product "
                f"not in edges {sorted(link_weight_tiers)}"
            )

        missing_tiers = price_weight_tiers - link_weight_tiers
        if missing_tiers:
            self.results["fixes_needed"].append(
                f"Product '{product_id}': prices exist for weight_tiers {sorted(missing_tiers)} but not in edges"
            )
        elif price_weight_tiers == link_weight_tiers:
            self.results["correct"].append(
                f"Product '{product_id}': all price weight_tiers match edges ({sorted(price_weight_tiers)})"
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

    def validate_products_in_edges(self) -> None:
        """Check for products not listed in graph.edges."""
        if self.graph is None:
            return

        edges = self.graph.get("edges", {})
        products_in_data = set(self.product_dict.keys())
        products_in_edges = set(edges.keys())
        missing_products = products_in_data - products_in_edges

        if missing_products:
            self.results["fixes_needed"].append(
                f"Products in products.json but not in edges: {sorted(missing_products)}"
            )
        else:
            self.results["correct"].append("All products are in edges")

    def validate_zones_and_weight_tiers(self) -> None:
        """Verify all zones and weight_tiers referenced in edges exist."""
        if self.graph is None:
            return

        edges = self.graph.get("edges", {})

        all_link_zones = set()
        all_link_weight_tiers = set()
        for edge_data in edges.values():
            all_link_zones.update(edge_data.get("zones", []))
            all_link_weight_tiers.update(edge_data.get("weight_tiers", []))

        invalid_zones = all_link_zones - set(self.zone_ids.keys())
        if not invalid_zones:
            self.results["correct"].append("All zones in edges are valid")

        invalid_weight_tiers = all_link_weight_tiers - self.weight_tier_ids
        if not invalid_weight_tiers:
            self.results["correct"].append("All weight_tiers in edges are valid")

    # ========================================================================
    # Services Validation
    # ========================================================================

    def validate_available_services(self) -> None:
        """Validate available_services and service-price consistency."""
        if self.graph is None:
            return

        available_services = self.graph.get("global_settings", {}).get("available_services", [])

        # Validate service existence
        valid_refs = self._service_refs_set()
        for sp in self.service_prices:
            sid = sp.get("service_id")
            if not sid:
                continue
            if str(sid) not in valid_refs:
                self.results["errors"].append(
                    f"Service '{sid}' in service_prices does not exist in {SERVICES_FILE} "
                    f"(by id or porto_id). Found in: {SERVICE_PRICES_FILE} -> service_prices"
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
                    f"Service '{service_id}' is listed as available but has no row in {SERVICE_PRICES_FILE}"
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
                        f"Price found in: {SERVICE_PRICES_FILE} -> service_prices. "
                        f"Service found in: {SERVICES_FILE} -> services"
                    )
                elif service_effective_to != price_effective_to:
                    self.results["errors"].append(
                        f"Service '{service_id}' has price effective_to='{price_effective_to}' "
                        f"but service effective_to='{service_effective_to}'. Dates must match. "
                        f"Price found in: {SERVICE_PRICES_FILE} -> service_prices. "
                        f"Service found in: {SERVICES_FILE} -> services"
                    )

    def validate_execution_semantics(self) -> None:
        """Validate mark_type / tracking_mode and optional tracking service linkage."""
        if self.products is None or self.services is None:
            return

        available_services = (self.graph or {}).get("global_settings", {}).get(
            "available_services"
        ) or []
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

            p_zones = frozenset(product.get("zones") or [])

            def _service_covers_product(
                svc: dict[str, Any],
                *,
                product_zones: frozenset[str] = p_zones,
            ) -> bool:
                sz = svc.get("supported_zones")
                if not sz:
                    return True
                return bool(set(product_zones) & set(sz))

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

    def validate_marks_profiles(self) -> None:
        """Validate marks.json default_profile, unique ids, and product.mark_profile references."""
        if self.products is None:
            return
        marks = self.marks
        if not marks or not isinstance(marks, dict):
            self.results["errors"].append(
                f"Missing or invalid {MARKS_FILE} (expected file_type marks)"
            )
            return
        if marks.get("file_type") != "marks":
            self.results["errors"].append(
                f"{MARKS_FILE}: file_type must be 'marks', got {marks.get('file_type')!r}"
            )
            return
        prov_graph = self.graph.get("provider") if self.graph else None
        prov_marks = marks.get("provider")
        if prov_graph and prov_marks and str(prov_graph) != str(prov_marks):
            self.results["errors"].append(
                f"{MARKS_FILE} provider '{prov_marks}' does not match graph provider '{prov_graph}'"
            )

        profiles_raw = marks.get("profiles")
        if not isinstance(profiles_raw, list) or not profiles_raw:
            self.results["errors"].append(f"{MARKS_FILE}: profiles must be a non-empty array")
            return

        by_id: dict[str, dict[str, Any]] = {}
        for row in profiles_raw:
            if not isinstance(row, dict) or not row.get("id"):
                self.results["errors"].append(
                    f"{MARKS_FILE}: each profile must be an object with id"
                )
                continue
            pid = str(row["id"])
            if pid in by_id:
                self.results["errors"].append(f"{MARKS_FILE}: duplicate profile id {pid!r}")
            by_id[pid] = row

        default_id = marks.get("default_profile")
        if not default_id or not isinstance(default_id, str):
            self.results["errors"].append(
                f"{MARKS_FILE}: default_profile must be a non-empty string"
            )
        elif default_id not in by_id:
            self.results["errors"].append(
                f"{MARKS_FILE}: default_profile {default_id!r} not found in profiles"
            )

        for product in self.products.get("products", []):
            if not isinstance(product, dict):
                continue
            product_id = product.get("id", "?")
            mp = product.get("mark_profile")
            chosen = str(mp) if isinstance(mp, str) and mp.strip() else default_id
            if not chosen:
                continue
            prof = by_id.get(chosen)
            if not prof:
                self.results["errors"].append(
                    f"Product '{product_id}': mark_profile {chosen!r} not found in {MARKS_FILE}"
                )
                continue
            p_mark = product.get("mark_type")
            pr_mark = prof.get("mark_type")
            if p_mark != pr_mark:
                self.results["errors"].append(
                    f"Product '{product_id}': mark_type {p_mark!r} does not match "
                    f"marks profile {chosen!r} mark_type {pr_mark!r}"
                )

    # ========================================================================
    # Provider rules (optional rules.json)
    # ========================================================================

    def validate_provider_rules(self) -> None:
        """Validate providers/<id>/rules.json when present (refs products, zones, services, prices)."""
        doc = self.provider_rules_doc
        if not doc:
            return
        if doc.get("file_type") != "provider_rules":
            self.results["errors"].append(
                f"rules.json: file_type must be 'provider_rules' (got {doc.get('file_type')!r})"
            )
            return
        prov = doc.get("provider")
        if self.graph and prov and str(prov) != str(self.graph.get("provider")):
            self.results["errors"].append(
                f"rules.json provider {prov!r} does not match graph provider "
                f"{self.graph.get('provider')!r}"
            )
        rules_raw = doc.get("rules")
        if not isinstance(rules_raw, list):
            self.results["errors"].append("rules.json: rules must be an array")
            return

        valid_refs = self._service_refs_set()
        service_price_ids = {
            str(sp.get("service_id")) for sp in self.service_prices if sp.get("service_id")
        }
        product_ids = set(self.product_dict.keys())
        unit_raw = doc.get("unit")
        unit_block: dict[str, Any] = unit_raw if isinstance(unit_raw, dict) else {}
        uses_thickness_metric = any(
            isinstance(r, dict)
            and r.get("kind") == PROVIDER_RULE_KIND_METRIC_BAND_ATTACH
            and str(r.get("metric") or "") == PROVIDER_RULE_METRIC_THICKNESS
            for r in rules_raw
        )
        if uses_thickness_metric and unit_block.get("thickness") != "mm":
            self.results["errors"].append(
                "rules.json: metric 'thickness' requires document unit.thickness 'mm' "
                f"(got {unit_block.get('thickness')!r})"
            )

        for rule in rules_raw:
            if not isinstance(rule, dict):
                self.results["errors"].append("rules.json: each rule must be an object")
                continue
            rid = rule.get("id", "?")
            kind = rule.get("kind")
            if kind != PROVIDER_RULE_KIND_METRIC_BAND_ATTACH:
                self.results["errors"].append(f"rules.json rule {rid!r}: unsupported kind {kind!r}")
                continue
            metric = rule.get("metric")
            if str(metric) != PROVIDER_RULE_METRIC_THICKNESS:
                self.results["errors"].append(
                    f"rules.json rule {rid!r}: unsupported metric {metric!r} "
                    f"(validator currently checks {PROVIDER_RULE_METRIC_THICKNESS!r} only)"
                )
                continue
            for pid in rule.get("product_ids") or []:
                if str(pid) not in product_ids:
                    self.results["errors"].append(
                        f"rules.json rule {rid!r}: unknown product_id {pid!r}"
                    )
            sid = rule.get("service_id")
            if not sid or str(sid) not in valid_refs:
                self.results["errors"].append(
                    f"rules.json rule {rid!r}: unknown service_id {sid!r}"
                )
            elif str(sid) not in service_price_ids:
                self.results["warnings"].append(
                    f"rules.json rule {rid!r}: service {sid!r} has no row in service_prices"
                )
            lo = rule.get("min_exclusive")
            hi = rule.get("max_inclusive")
            if not isinstance(lo, (int, float)) or not isinstance(hi, (int, float)):
                self.results["errors"].append(
                    f"rules.json rule {rid!r}: min_exclusive and max_inclusive must be numbers"
                )
            elif lo >= hi:
                self.results["errors"].append(
                    f"rules.json rule {rid!r}: min_exclusive must be < max_inclusive"
                )

        if not self.results["errors"]:
            self.results["correct"].append(
                "rules.json references are consistent with catalog and prices"
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

        graph_weight = self.graph.get("unit", {}).get("weight")
        products_weight = self.products.get("unit", {}).get("weight")
        weight_tiers_weight = self.weight_tiers.get("unit", {}).get("weight")

        validate_unit_consistency(
            unit_name="weight",
            graph_unit_value=graph_weight,
            expected_value=EXPECTED_WEIGHT_UNIT,
            file_names=[GRAPH_FILE, PRODUCTS_FILE, WEIGHTS_FILE],
            results=self.results,
            other_values=[products_weight, weight_tiers_weight],
        )

    def validate_dimension_units(self) -> None:
        """Validate dimension unit co nsistency (graph + global envelopes; products.json has no linear dimension unit)."""
        if not all([self.graph, self.envelopes]):
            return

        assert self.graph is not None
        assert self.envelopes is not None

        graph_dimension = self.graph.get("unit", {}).get("dimension")
        formats_dimension = self.envelopes.get("unit", {}).get("dimension")

        layouts_dimension = None
        if self.envelope_layouts:
            layouts_dimension = self.envelope_layouts.get("unit", {}).get("dimension")

        validate_unit_consistency(
            unit_name="dimension",
            graph_unit_value=graph_dimension,
            expected_value=EXPECTED_DIMENSION_UNIT,
            file_names=[GRAPH_FILE, ENVELOPES_FILE, LAYOUTS_FILE],
            results=self.results,
            other_values=[formats_dimension, layouts_dimension],
        )

    def _resolve_envelope_layout_row(
        self,
        jurisdictions: dict[str, Any],
        cc: str,
        eid: str,
    ) -> dict[str, Any] | None:
        """Return row with orientation+layout or None."""
        j = jurisdictions.get(cc)
        if not isinstance(j, dict):
            return None
        envs = j.get("envelopes")
        if not isinstance(envs, dict):
            return None
        row = envs.get(eid)
        if not isinstance(row, dict):
            return None
        if row.get("layout") is not None and row.get("orientation") is not None:
            return row
        return None

    def validate_envelope_layout_references(self) -> None:
        """Jurisdiction keys, envelope ids, each row must define orientation+layout."""
        if not self.envelope_layouts or not self.envelopes:
            return

        assert self.envelope_layouts is not None
        assert self.envelopes is not None

        format_ids = {
            f["id"]
            for f in self.envelopes.get("envelopes", [])
            if isinstance(f, dict) and f.get("id")
        }
        jurisdictions = self.envelope_layouts.get("jurisdictions")
        if not isinstance(jurisdictions, dict):
            return

        for cc, jblock in jurisdictions.items():
            if not isinstance(jblock, dict):
                continue
            envs = jblock.get("envelopes")
            if not isinstance(envs, dict):
                continue
            for eid, row in envs.items():
                if eid not in format_ids:
                    self.results["errors"].append(
                        f"{LAYOUTS_FILE}: jurisdictions.{cc}.envelopes "
                        f"unknown envelope id {eid!r} (not in {ENVELOPES_FILE})"
                    )
                if not isinstance(row, dict):
                    continue
                resolved = self._resolve_envelope_layout_row(jurisdictions, str(cc), str(eid))
                if resolved is None:
                    self.results["errors"].append(
                        f"{LAYOUTS_FILE}: jurisdictions.{cc}.envelopes.{eid} "
                        "must define orientation and layout"
                    )

    def validate_envelope_address_window(self) -> None:
        """address_area must match window (or print_area when no window) for resolved layouts."""
        if not self.envelope_layouts:
            return
        jurisdictions = self.envelope_layouts.get("jurisdictions")
        if not isinstance(jurisdictions, dict):
            return

        for cc, jblock in jurisdictions.items():
            if not isinstance(jblock, dict):
                continue
            envs = jblock.get("envelopes")
            if not isinstance(envs, dict):
                continue
            for eid in envs:
                row = self._resolve_envelope_layout_row(jurisdictions, str(cc), str(eid))
                if not row or not isinstance(row, dict):
                    continue
                fid = str(eid)
                env = {"layout": row.get("layout")}
                path = f"{LAYOUTS_FILE} ({cc}, {fid})"
                v = _envelope_validation_views(env)
                addr = v["addr"]
                pa = v["pa"]
                wa = v["wa"]
                has_w = v["has_w"]
                no_window = v["no_window"]
                force_window = v["force_window"]
                if not _envelope_rect_complete(addr):
                    self.results["errors"].append(
                        f"Layout '{fid}' ({path}): address_area must have integer x, y, width, height"
                    )
                    continue
                if not _envelope_rect_complete(pa):
                    self.results["errors"].append(
                        f"Layout '{fid}' ({path}): print_area must have integer x, y, width, height"
                    )
                    continue
                if no_window and force_window:
                    self.results["errors"].append(
                        f"Layout '{fid}' ({path}): supports_window is false but window_supported is true"
                    )
                    continue
                assert isinstance(addr, dict) and isinstance(pa, dict)
                if no_window:
                    if has_w:
                        self.results["errors"].append(
                            f"Layout '{fid}' ({path}): supports_window is false; omit window_area"
                        )
                    elif not _envelope_rect_equal(addr, pa):
                        self.results["errors"].append(
                            f"Layout '{fid}' ({path}): without window, address_area must equal print_area"
                        )
                elif force_window:
                    if not has_w:
                        self.results["errors"].append(
                            f"Layout '{fid}' ({path}): window_supported true requires window_area"
                        )
                    elif not isinstance(wa, dict) or not _envelope_rect_equal(addr, wa):
                        self.results["errors"].append(
                            f"Layout '{fid}' ({path}): address_area must equal window_area "
                            "(identical x,y,width,height)"
                        )
                elif has_w:
                    assert isinstance(wa, dict)
                    if not _envelope_rect_equal(addr, wa):
                        self.results["errors"].append(
                            f"Layout '{fid}' ({path}): address_area must equal window_area "
                            "(identical x,y,width,height)"
                        )
                elif not _envelope_rect_equal(addr, pa):
                    self.results["errors"].append(
                        f"Layout '{fid}' ({path}): no window_area; address_area must equal print_area"
                    )

    def validate_product_envelope_format_ids(self) -> None:
        """products.envelope_ids must exist in global envelopes.json."""
        if not self.envelopes or not self.products:
            return

        assert self.envelopes is not None
        assert self.products is not None

        format_ids = {
            f["id"]
            for f in self.envelopes.get("envelopes", [])
            if isinstance(f, dict) and f.get("id")
        }
        for p in self.products.get("products", []):
            if not isinstance(p, dict):
                continue
            pid = p.get("id", "?")
            for eid in p.get("envelope_ids") or []:
                if eid not in format_ids:
                    self.results["errors"].append(
                        f"Product '{pid}': envelope_id {eid!r} not found in {ENVELOPES_FILE}"
                    )

    def validate_price_units(self) -> None:
        """Validate price unit consistency."""
        if not all([self.graph, self.product_prices_doc]):
            return

        assert self.graph is not None
        assert self.product_prices_doc is not None

        graph_price = self.graph.get("unit", {}).get("price")
        pp_price = self.product_prices_doc.get("unit", {}).get("price")
        sp_price = (
            self.service_prices_doc.get("unit", {}).get("price")
            if self.service_prices_doc
            else None
        )

        validate_unit_consistency(
            unit_name="price",
            graph_unit_value=graph_price,
            expected_value=EXPECTED_PRICE_UNIT,
            file_names=[GRAPH_FILE, PRODUCT_PRICES_FILE, SERVICE_PRICES_FILE],
            results=self.results,
            other_values=[pp_price, sp_price],
        )

    def validate_currency_units(self) -> None:
        """Validate currency unit consistency."""
        if not all([self.graph, self.product_prices_doc]):
            return

        assert self.graph is not None
        assert self.product_prices_doc is not None

        graph_currency = self.graph.get("unit", {}).get("currency")
        pp_currency = self.product_prices_doc.get("unit", {}).get("currency")
        sp_currency = (
            self.service_prices_doc.get("unit", {}).get("currency")
            if self.service_prices_doc
            else None
        )
        expected_ccy = str(graph_currency) if graph_currency else EXPECTED_CURRENCY

        validate_unit_consistency(
            unit_name="currency",
            graph_unit_value=graph_currency,
            expected_value=expected_ccy,
            file_names=[GRAPH_FILE, PRODUCT_PRICES_FILE, SERVICE_PRICES_FILE],
            results=self.results,
            other_values=[pp_currency, sp_currency],
        )

    # ========================================================================
    # Circular Dependencies Validation
    # ========================================================================

    def validate_circular_dependencies(self) -> None:
        """Check for circular dependencies."""
        if self.graph is None:
            return

        dependencies = self.graph.get("dependencies", {})
        if not isinstance(dependencies, dict):
            return

        file_ref_to_dep: dict[str, str] = {}
        for dep_name, dep_data in dependencies.items():
            df = dep_data.get("file") if isinstance(dep_data, dict) else None
            if isinstance(df, str) and df:
                file_ref_to_dep[df] = dep_name

        dep_graph: dict[str, set[str]] = {}
        for dep_name, dep_data in dependencies.items():
            if not isinstance(dep_data, dict):
                continue
            resolved: set[str] = set()
            for d in dep_data.get("depends_on", []) or []:
                if not isinstance(d, str):
                    continue
                target = file_ref_to_dep.get(d)
                if target:
                    resolved.add(target)
            dep_graph[dep_name] = resolved

        if "products" in dep_graph.get(
            "product_prices", set()
        ) and "product_prices" in dep_graph.get("products", set()):
            self.results["warnings"].append(
                "Circular dependency: products ↔ product_prices — review intentional or not."
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
        self.validate_edges()
        self.validate_products_in_edges()
        self.validate_zones_and_weight_tiers()
        self.validate_available_services()
        self.validate_execution_semantics()
        self.validate_marks_profiles()
        self.validate_provider_rules()
        self.validate_dependencies()
        self.validate_units()
        self.validate_envelope_layout_references()
        self.validate_envelope_address_window()
        self.validate_product_envelope_format_ids()
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
        data_dir: Path to data directory (single-directory layout). If None, uses project_root + provider.
        project_root: Path to porto_data root (with policy/, mails/, providers/). Defaults to get_project_root().
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
