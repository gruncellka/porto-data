"""Helper functions for validators - shared validation logic."""

from scripts.validators.base import ValidationResults


def validate_unit_consistency(
    unit_name: str,
    data_links_value: str | None,
    expected_value: str,
    file_names: list[str],
    results: ValidationResults,
    other_values: list[str | None],
) -> None:
    """Validate unit consistency across multiple files.

    Args:
        unit_name: Name of the unit being validated (e.g., "weight", "dimension").
        data_links_value: Unit value from data_links.json.
        expected_value: Expected unit value.
        file_names: List of file names for error messages.
        results: Validation results dictionary to update.
        other_values: List of unit values from other files to compare.
    """
    all_values = [data_links_value] + other_values

    # Check if all values are the same
    if len(set(all_values)) == 1:
        if data_links_value == expected_value:
            results["correct"].append(
                f"Unit {unit_name} '{expected_value}' is consistent across all files"
            )
        else:
            results["warnings"].append(
                f"Unit {unit_name} '{data_links_value}' is consistent but verify it's correct. "
                f"Expected: '{expected_value}'. "
                f"Found in: {', '.join(file_names)} -> unit -> {unit_name}"
            )
    else:
        value_str = ", ".join(f"{name}={val}" for name, val in zip(file_names, all_values))
        results["errors"].append(
            f"{unit_name.capitalize()} unit mismatch: {value_str}. Expected: '{expected_value}'"
        )
