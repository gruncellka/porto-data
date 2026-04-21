"""CLI-style entrypoint and human-readable result printing."""

from __future__ import annotations

from pathlib import Path

from scripts.data_files import DEFAULT_PROVIDER
from scripts.validators.base import ValidationResults

from .validator import GraphValidator


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

    total_issues = len(results["errors"]) + len(results["fixes_needed"]) + len(results["warnings"])
    if total_issues == 0:
        print("🎉 All checks passed! graph.json is correct.")
        return 0
    print(
        f"📊 Summary: {len(results['errors'])} errors, "
        f"{len(results['fixes_needed'])} fixes needed, "
        f"{len(results['warnings'])} warnings"
    )
    return 1 if results["errors"] else 0
