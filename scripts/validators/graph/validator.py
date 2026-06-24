"""GraphValidator — loads data and orchestrates graph.json validation."""

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
    load_providers_registry,
    market_for_country,
)
from scripts.utils import load_json
from scripts.validators.base import ValidationResults

from .dependencies import (
    run_validate_cycles,
    run_validate_dependencies,
    run_validate_price_dependencies,
)
from .edges import (
    run_validate_edge_tiers,
    run_validate_edges,
    run_validate_products_in_edges,
)
from .execution_semantics import run_validate_execution_semantics
from .layouts import (
    run_validate_envelope_address_window,
    run_validate_envelope_ids,
    run_validate_layout_refs,
)
from .mark_edges import run_validate_mark_edges
from .marks_profiles import run_validate_marks_profiles
from .provider_rules import run_validate_provider_rules
from .services import run_validate_graph_services
from .units import run_validate_units


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
            project_root: Path to porto_data root (with policy/, formats/, providers/).
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
        self.market: dict[str, Any] | None = None

        self.product_dict: dict[str, dict[str, Any]] = {}
        self.zone_ids: dict[str, dict[str, Any]] = {}
        self.weight_tier_ids: set[str] = set()
        self.service_ids: dict[str, dict[str, Any]] = {}
        self.services_by_id: dict[str, dict[str, Any]] = {}
        self.product_prices: list[dict[str, Any]] = []
        self.service_prices: list[dict[str, Any]] = []
        self.all_data_files: set[str] = set()

    def load_data(self) -> None:
        """Load all required JSON files and build lookup structures."""
        if self.graph is not None:
            return

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
            self._load_market_for_provider()
        except FileNotFoundError as e:
            self.results["errors"].append(f"Missing file: {str(e)}")
            return
        except json.JSONDecodeError as e:
            self.results["errors"].append(f"Invalid JSON: {str(e)}")
            return

        self._build_lookup_structures()

    def _load_market_for_provider(self) -> None:
        """Resolve policy/markets.json row for this provider's registry country."""
        if self.graph is None:
            return
        provider_id = self.graph.get("provider") or self.provider_dir.name
        try:
            reg = load_providers_registry()
            row = reg.get("providers", {}).get(provider_id)
            if isinstance(row, dict) and isinstance(row.get("country"), str):
                self.market = market_for_country(str(row["country"]))
        except (FileNotFoundError, ValueError):
            self.market = None

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
        pp_raw = (
            self.product_prices_doc.get("product_prices", []) if self.product_prices_doc else []
        )
        sp_raw = (
            self.service_prices_doc.get("service_prices", []) if self.service_prices_doc else []
        )
        self.product_prices = pp_raw if isinstance(pp_raw, list) else []
        self.service_prices = sp_raw if isinstance(sp_raw, list) else []
        if self.shared_bundle_subdir == self._bundle_root:
            self.all_data_files = {
                p.relative_to(self.data_dir).as_posix() for p in self.data_dir.rglob("*.json")
            }
        else:
            self.all_data_files = get_graph_dependency_file_refs(self.provider_dir.name)

    def validate_price_dependencies(self) -> None:
        """Validate price file paths (dependencies) and price row join keys."""
        if self.graph is None:
            return
        run_validate_price_dependencies(
            self.results,
            graph=self.graph,
            shared_bundle_subdir=self.shared_bundle_subdir,
            bundle_root=self._bundle_root,
            provider_dir=self.provider_dir,
            all_data_files=self.all_data_files,
            product_prices_doc=self.product_prices_doc,
            service_prices_doc=self.service_prices_doc,
            product_prices=self.product_prices,
            service_prices=self.service_prices,
        )

    def validate_edges(self) -> None:
        """Validate graph.edges: per-product zones and weight_tiers."""
        if self.graph is None:
            return
        run_validate_edges(
            self.results,
            graph=self.graph,
            product_dict=self.product_dict,
            zone_ids=self.zone_ids,
            weight_tier_ids=self.weight_tier_ids,
            product_prices=self.product_prices,
        )

    def validate_products_in_edges(self) -> None:
        """Check for products not listed in graph.edges."""
        if self.graph is None:
            return
        run_validate_products_in_edges(
            self.results,
            graph=self.graph,
            product_dict=self.product_dict,
        )

    def validate_zones_and_weight_tiers(self) -> None:
        """Verify all zones and weight_tiers referenced in edges exist."""
        if self.graph is None:
            return
        run_validate_edge_tiers(
            self.results,
            graph=self.graph,
            zone_ids=self.zone_ids,
            weight_tier_ids=self.weight_tier_ids,
        )

    def validate_services(self) -> None:
        """Validate services and service-price consistency."""
        if self.graph is None:
            return
        run_validate_graph_services(
            self.results,
            graph=self.graph,
            services=self.services,
            service_prices=self.service_prices,
        )

    def validate_execution_semantics(self) -> None:
        """Validate mark_type / tracking_mode and optional tracking service linkage."""
        run_validate_execution_semantics(
            self.results,
            graph=self.graph,
            products=self.products,
            services=self.services,
            services_by_id=self.services_by_id,
            product_dict=self.product_dict,
        )

    def validate_marks_profiles(self) -> None:
        """Validate marks.json profile catalog and default_profile."""
        run_validate_marks_profiles(
            self.results,
            graph=self.graph,
            products=self.products,
            marks=self.marks,
            zones=self.zones,
            services=self.services,
        )

    def validate_mark_edges(self) -> None:
        """Validate graph.mark_edges zone and service mark profile resolution."""
        run_validate_mark_edges(
            self.results,
            graph=self.graph,
            marks=self.marks,
            zones=self.zones,
        )

    def validate_provider_rules(self) -> None:
        """Validate providers/<id>/rules.json when present (refs products, zones, services, prices)."""
        run_validate_provider_rules(
            self.results,
            graph=self.graph,
            doc=self.provider_rules_doc,
            product_dict=self.product_dict,
            service_prices=self.service_prices,
            services=self.services,
        )

    def validate_dependencies(self) -> None:
        """Validate dependencies section."""
        if self.graph is None:
            return
        run_validate_dependencies(
            self.results,
            graph=self.graph,
            all_data_files=self.all_data_files,
        )

    def validate_units(self) -> None:
        """Validate all unit values consistency."""
        run_validate_units(
            self.results,
            graph=self.graph,
            products=self.products,
            weight_tiers=self.weight_tiers,
            envelopes=self.envelopes,
            envelope_layouts=self.envelope_layouts,
            product_prices_doc=self.product_prices_doc,
            service_prices_doc=self.service_prices_doc,
            market=self.market,
        )

    def validate_envelope_layout_references(self) -> None:
        """Jurisdiction keys, envelope ids, each row must define orientation+layout."""
        run_validate_layout_refs(
            self.results,
            envelope_layouts=self.envelope_layouts,
            envelopes=self.envelopes,
        )

    def validate_envelope_address_window(self) -> None:
        """window.area consistency for resolved layouts."""
        run_validate_envelope_address_window(
            self.results,
            envelope_layouts=self.envelope_layouts,
        )

    def validate_product_envelope_format_ids(self) -> None:
        """products.envelope_ids must exist in global envelopes.json."""
        run_validate_envelope_ids(
            self.results,
            envelopes=self.envelopes,
            products=self.products,
        )

    def validate_circular_dependencies(self) -> None:
        """Check for circular dependencies."""
        if self.graph is None:
            return
        run_validate_cycles(self.results, graph=self.graph)

    def validate_all(self) -> ValidationResults:
        """Run all validations in logical order.

        Returns:
            ValidationResults dictionary with errors, warnings, fixes_needed, and correct items.
        """
        self.load_data()

        if self.results["errors"]:
            return self.results

        self.validate_price_dependencies()
        self.validate_edges()
        self.validate_products_in_edges()
        self.validate_zones_and_weight_tiers()
        self.validate_services()
        self.validate_execution_semantics()
        self.validate_marks_profiles()
        self.validate_mark_edges()
        self.validate_provider_rules()
        self.validate_dependencies()
        self.validate_units()
        self.validate_envelope_layout_references()
        self.validate_envelope_address_window()
        self.validate_product_envelope_format_ids()
        self.validate_circular_dependencies()

        return self.results
