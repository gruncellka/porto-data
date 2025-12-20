"""Validate command for porto CLI."""

import sys
from pathlib import Path

# Add scripts to path for imports
_project_root = Path(__file__).parent.parent.parent
_scripts_dir = _project_root / "scripts"
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

from validators.base import ValidationResults
from validators.links import DataLinksValidator
from validators.schema import validate_all_schemas


def print_error(message: str) -> None:
    """Print error message to stderr."""
    print(f"❌ ERROR: {message}", file=sys.stderr)


def print_warning(message: str) -> None:
    """Print warning message."""
    print(f"⚠️  WARNING: {message}")


def print_fix_needed(message: str) -> None:
    """Print fix needed message."""
    print(f"🔧 FIX NEEDED: {message}")


def print_success(message: str) -> None:
    """Print success message."""
    print(f"✅ {message}")


def print_validate_mode(results: ValidationResults) -> int:
    """Print results in validate mode (CI/CD friendly)."""
    print("Validating data_links.json against data files...\n")

    has_errors = len(results["errors"]) > 0
    has_issues = (
        len(results["errors"]) + len(results["fixes_needed"]) + len(results["warnings"]) > 0
    )

    if results["errors"]:
        for error in results["errors"]:
            print_error(error)
        print()

    if results["fixes_needed"]:
        for fix in results["fixes_needed"]:
            print_fix_needed(fix)
        print()

    if results["warnings"]:
        for warning in results["warnings"]:
            print_warning(warning)
        print()

    if not has_errors and not has_issues:
        print_success("All validations passed! data_links.json is consistent with data files.")
        return 0
    elif not has_errors:
        print_success("No critical errors found, but there are warnings to review.")
        return 0
    else:
        print_error("Validation failed. Please fix the errors above.")
        return 1


def print_analyze_mode(results: ValidationResults) -> int:
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


def validate_schema() -> int:
    """Validate JSON schemas.

    Returns:
        Exit code: 0 if validation passes, 1 otherwise.
    """
    result: int = validate_all_schemas()
    if result != 0:
        return result

    # Handle metadata generation after successful validation
    from cli.commands.metadata import handle_metadata_generation

    metadata_result = handle_metadata_generation()
    return metadata_result


def validate_links(analyze: bool = False) -> int:
    """Validate data links.

    Args:
        analyze: If True, show detailed analysis. If False, show CI/CD friendly output.

    Returns:
        Exit code: 0 if validation passes, 1 otherwise.
    """
    # Get project root
    _project_root = Path(__file__).parent.parent.parent
    data_dir = _project_root / "data"

    validator = DataLinksValidator(data_dir)
    results = validator.validate_all()

    if analyze:
        return print_analyze_mode(results)
    else:
        return print_validate_mode(results)


def validate_all() -> int:
    """Validate everything (schemas and links).

    Returns:
        Exit code: 0 if all validations pass, 1 otherwise.
    """
    schema_result = validate_schema()
    if schema_result != 0:
        return schema_result

    links_result = validate_links(analyze=False)
    return links_result
