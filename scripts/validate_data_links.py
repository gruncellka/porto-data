#!/usr/bin/env python3
"""
Validate and analyze data_links.json against actual data files.
Checks for consistency, missing references, and logical errors.

Usage:
    python validate_data_links.py          # Validate mode (CI/CD friendly)
    python validate_data_links.py --analyze # Detailed analysis mode
"""

import argparse
import json
import sys
from pathlib import Path

from utils import get_data_files, load_json

# Get project root
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"


def validate_and_analyze_data_links() -> dict[str, list[str]]:
    """Comprehensive validation and analysis of data_links.json."""
    results: dict[str, list[str]] = {
        "errors": [],
        "warnings": [],
        "fixes_needed": [],
        "correct": [],
    }

    # Load all data files
    try:
        data_links = load_json(DATA_DIR / "data_links.json")
        products = load_json(DATA_DIR / "products.json")
        zones = load_json(DATA_DIR / "zones.json")
        weight_tiers = load_json(DATA_DIR / "weight_tiers.json")
        services = load_json(DATA_DIR / "services.json")
        prices = load_json(DATA_DIR / "prices.json")
    except FileNotFoundError as e:
        results["errors"].append(f"Missing file: {str(e)}")
        return results
    except json.JSONDecodeError as e:
        results["errors"].append(f"Invalid JSON: {str(e)}")
        return results

    # Extract IDs for quick lookup
    product_dict = {p["id"]: p for p in products.get("products", [])}
    zone_ids = {z["id"]: z for z in zones.get("zones", [])}
    weight_tier_ids = set(weight_tiers.get("weight_tiers", {}).keys())
    service_ids = {s["id"]: s for s in services.get("services", [])}
    product_prices = prices.get("prices", {}).get("product_prices", [])
    service_prices = prices.get("prices", {}).get("service_prices", [])

    # 1. Verify lookup_method array path matches actual structure
    lookup_array = data_links.get("global_settings", {}).get("lookup_method", {}).get("array", "")
    if lookup_array == "prices.product_prices":
        if "prices" in prices and "product_prices" in prices["prices"]:
            results["correct"].append(
                "lookup_method.array 'prices.product_prices' matches actual structure"
            )
        else:
            results["errors"].append(
                "Lookup method references 'prices.product_prices' but structure doesn't match"
            )
    else:
        results["warnings"].append(
            f"Lookup method array path '{lookup_array}' - verify this matches actual structure"
        )

    # 2. Validate links section
    links = data_links.get("links", {})
    for product_id, link_data in links.items():
        # Check if product exists
        if product_id not in product_dict:
            results["errors"].append(
                f"Product '{product_id}' in links does not exist in products.json"
            )
            continue

        product = product_dict[product_id]
        link_zones = set(link_data.get("zones", []))
        link_weight_tiers = set(link_data.get("weight_tiers", []))
        product_zones = set(product.get("supported_zones", []))
        product_weight_tier = product.get("weight_tier")

        # Validate zones
        for zone in link_zones:
            if zone not in zone_ids:
                results["errors"].append(
                    f"Zone '{zone}' for product '{product_id}' does not exist in zones.json"
                )

        # Check if zones match
        if link_zones == product_zones:
            results["correct"].append(f"Product '{product_id}': zones match ({sorted(link_zones)})")
        else:
            results["fixes_needed"].append(
                f"Product '{product_id}': zones mismatch - links: {sorted(link_zones)}, product: {sorted(product_zones)}"
            )

        # Validate weight_tiers
        for wt in link_weight_tiers:
            if wt not in weight_tier_ids:
                results["errors"].append(
                    f"Weight tier '{wt}' for product '{product_id}' does not exist in weight_tiers.json"
                )

        # Find all weight tiers that have prices for this product
        price_weight_tiers = {
            p["weight_tier"] for p in product_prices if p.get("product_id") == product_id
        }

        # Check if product's weight_tier is in links
        if product_weight_tier and product_weight_tier in link_weight_tiers:
            results["correct"].append(
                f"Product '{product_id}': weight_tier '{product_weight_tier}' is in links"
            )
        elif product_weight_tier:
            results["fixes_needed"].append(
                f"Product '{product_id}': weight_tier '{product_weight_tier}' from product not in links {sorted(link_weight_tiers)}"
            )

        # Check if all price weight_tiers are in links
        missing_tiers = price_weight_tiers - link_weight_tiers
        if missing_tiers:
            results["fixes_needed"].append(
                f"Product '{product_id}': prices exist for weight_tiers {sorted(missing_tiers)} but not in links"
            )
        elif price_weight_tiers == link_weight_tiers:
            results["correct"].append(
                f"Product '{product_id}': all price weight_tiers match links ({sorted(price_weight_tiers)})"
            )

        # Check if there are prices for all zone+weight_tier combinations
        for zone in link_zones:
            for weight_tier in link_weight_tiers:
                matching_price = any(
                    p.get("product_id") == product_id
                    and p.get("zone") == zone
                    and p.get("weight_tier") == weight_tier
                    for p in product_prices
                )
                if not matching_price:
                    results["warnings"].append(
                        f"No price found for product '{product_id}', zone '{zone}', weight_tier '{weight_tier}'"
                    )

    # 3. Check for products not in links
    products_in_data = set(product_dict.keys())
    products_in_links = set(links.keys())
    missing_products = products_in_data - products_in_links
    if missing_products:
        results["fixes_needed"].append(
            f"Products in products.json but not in links: {sorted(missing_products)}"
        )
    else:
        results["correct"].append("All products are in links")

    # 4. Verify all zones in links exist (already checked above, but summary)
    all_link_zones = set()
    for link_data in links.values():
        all_link_zones.update(link_data.get("zones", []))

    invalid_zones = all_link_zones - set(zone_ids.keys())
    if not invalid_zones:
        results["correct"].append("All zones in links are valid")

    # 5. Verify all weight_tiers in links exist (already checked above, but summary)
    all_link_weight_tiers = set()
    for link_data in links.values():
        all_link_weight_tiers.update(link_data.get("weight_tiers", []))

    invalid_weight_tiers = all_link_weight_tiers - weight_tier_ids
    if not invalid_weight_tiers:
        results["correct"].append("All weight_tiers in links are valid")

    # 6. Validate available_services
    available_services = data_links.get("global_settings", {}).get("available_services", [])
    for service_id in available_services:
        if service_id not in service_ids:
            results["errors"].append(
                f"Service '{service_id}' in available_services does not exist in services.json"
            )

    # Check if all services have prices
    service_price_ids = {sp.get("service_id") for sp in service_prices}
    for service_id in available_services:
        if service_id not in service_price_ids:
            results["warnings"].append(
                f"Service '{service_id}' is listed as available but has no price in prices.json"
            )

    # 7. Validate dependencies section
    dependencies = data_links.get("dependencies", {})
    all_data_files = get_data_files()

    for dep_name, dep_data in dependencies.items():
        dep_file = dep_data.get("file")
        if dep_file not in all_data_files:
            results["warnings"].append(f"Dependency file '{dep_file}' is not a known data file")

        depends_on = dep_data.get("depends_on", [])
        for dep_file_name in depends_on:
            if dep_file_name not in all_data_files:
                results["warnings"].append(
                    f"Dependency '{dep_file_name}' in '{dep_name}' is not a known data file"
                )

    # 8. Check for circular dependencies
    dep_graph: dict[str, set[str]] = {}
    for _dep_name, dep_data in dependencies.items():
        dep_file = dep_data.get("file", "").replace(".json", "")
        depends_on = {d.replace(".json", "") for d in dep_data.get("depends_on", [])}
        dep_graph[dep_file] = depends_on

    # Simple circular dependency check (products -> prices -> products)
    if "products" in dep_graph.get("prices", set()) and "prices" in dep_graph.get(
        "products", set()
    ):
        results["warnings"].append(
            "Circular dependency detected: products depends on prices, and prices depends on products. "
            "This may be intentional but should be reviewed."
        )

    return results


def print_validate_mode(results: dict[str, list[str]]) -> int:
    """Print results in validate mode (CI/CD friendly)."""
    print("Validating data_links.json against data files...\n")

    has_errors = len(results["errors"]) > 0
    has_issues = (
        len(results["errors"]) + len(results["fixes_needed"]) + len(results["warnings"]) > 0
    )

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

    if not has_errors and not has_issues:
        print("✅ All validations passed! data_links.json is consistent with data files.")
        return 0
    elif not has_errors:
        print("✅ No critical errors found, but there are warnings to review.")
        return 0
    else:
        print("❌ Validation failed. Please fix the errors above.")
        return 1


def print_analyze_mode(results: dict[str, list[str]]) -> int:
    """Print results in analyze mode (detailed report)."""
    print("=" * 70)
    print("COMPREHENSIVE DATA_LINKS.JSON ANALYSIS")
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
        print("🎉 All checks passed! data_links.json is correct.")
        return 0
    else:
        print(
            f"📊 Summary: {len(results['errors'])} errors, "
            f"{len(results['fixes_needed'])} fixes needed, "
            f"{len(results['warnings'])} warnings"
        )
        return 1 if results["errors"] else 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate and analyze data_links.json against data files"
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Show detailed analysis (default: validate mode for CI/CD)",
    )
    args = parser.parse_args()

    results = validate_and_analyze_data_links()

    if args.analyze:
        return print_analyze_mode(results)
    else:
        return print_validate_mode(results)


if __name__ == "__main__":
    sys.exit(main())
