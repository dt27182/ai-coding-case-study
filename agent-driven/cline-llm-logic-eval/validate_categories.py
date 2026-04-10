"""
Category Data Validation Script
Validates that category data meets requirements:
- 20 categories defined
- 20 values per category
- No duplicate values within each category
"""

from category_data import CATEGORY_NAMES, VALUE_POOLS


def validate_categories():
    """
    Validate category data for completeness and correctness.
    
    Returns:
        True if all validations pass, False otherwise
    """
    all_valid = True
    
    # Validation 1: Check there are exactly 20 categories
    print("=" * 80)
    print("VALIDATION 1: Number of Categories")
    print("=" * 80)
    
    num_categories = len(CATEGORY_NAMES)
    print(f"Total categories defined: {num_categories}")
    
    if num_categories == 20:
        print("✓ PASS: Exactly 20 categories defined")
    else:
        print(f"✗ FAIL: Expected 20 categories, found {num_categories}")
        all_valid = False
    
    print()
    
    # Validation 2: Check each category has exactly 20 values
    print("=" * 80)
    print("VALIDATION 2: Number of Values per Category")
    print("=" * 80)
    
    categories_with_wrong_count = []
    
    for category in CATEGORY_NAMES:
        if category not in VALUE_POOLS:
            print(f"✗ ERROR: Category '{category}' is in CATEGORY_NAMES but not in VALUE_POOLS")
            all_valid = False
            continue
        
        values = VALUE_POOLS[category]
        value_count = len(values)
        
        if value_count != 20:
            categories_with_wrong_count.append((category, value_count))
            print(f"✗ FAIL: Category '{category}' has {value_count} values (expected 20)")
            all_valid = False
    
    if not categories_with_wrong_count:
        print(f"✓ PASS: All {num_categories} categories have exactly 20 values")
    else:
        print(f"\nSummary: {len(categories_with_wrong_count)} categories with wrong value count")
    
    print()
    
    # Validation 3: Check for duplicate values within each category
    print("=" * 80)
    print("VALIDATION 3: No Duplicate Values within Categories")
    print("=" * 80)
    
    categories_with_duplicates = []
    
    for category in CATEGORY_NAMES:
        if category not in VALUE_POOLS:
            continue
        
        values = VALUE_POOLS[category]
        unique_values = set(values)
        
        if len(values) != len(unique_values):
            # Find duplicates
            seen = set()
            duplicates = set()
            for value in values:
                if value in seen:
                    duplicates.add(value)
                seen.add(value)
            
            categories_with_duplicates.append((category, list(duplicates)))
            print(f"✗ FAIL: Category '{category}' has duplicate values: {list(duplicates)}")
            all_valid = False
    
    if not categories_with_duplicates:
        print(f"✓ PASS: All categories have unique values (no duplicates)")
    else:
        print(f"\nSummary: {len(categories_with_duplicates)} categories with duplicates")
    
    print()
    
    # Extra validation: Check for categories in VALUE_POOLS not in CATEGORY_NAMES
    print("=" * 80)
    print("EXTRA VALIDATION: Consistency Check")
    print("=" * 80)
    
    extra_categories = set(VALUE_POOLS.keys()) - set(CATEGORY_NAMES)
    
    if extra_categories:
        print(f"⚠ WARNING: Categories in VALUE_POOLS but not in CATEGORY_NAMES: {extra_categories}")
    else:
        print("✓ PASS: All VALUE_POOLS categories are in CATEGORY_NAMES")
    
    print()
    
    # Final summary
    print("=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    
    if all_valid:
        print("✓ ALL VALIDATIONS PASSED")
        print(f"  - {num_categories} categories defined")
        print(f"  - All categories have 20 values")
        print(f"  - No duplicate values found")
        return True
    else:
        print("✗ SOME VALIDATIONS FAILED")
        print("  Please review the errors above and fix the category_data.py file")
        return False


def print_category_summary():
    """Print a summary of all categories and their value counts."""
    print("\n" + "=" * 80)
    print("CATEGORY SUMMARY")
    print("=" * 80)
    print(f"{'Category':<15} {'Value Count':<15} {'Status':<10}")
    print("-" * 80)
    
    for category in CATEGORY_NAMES:
        if category in VALUE_POOLS:
            count = len(VALUE_POOLS[category])
            status = "OK" if count == 20 else "ISSUE"
            print(f"{category:<15} {count:<15} {status:<10}")
        else:
            print(f"{category:<15} {'N/A':<15} {'MISSING':<10}")
    
    print()


if __name__ == "__main__":
    print("\nCategory Data Validation Script")
    print("=" * 80)
    print()
    
    # Run validations
    is_valid = validate_categories()
    
    # Print detailed summary
    print_category_summary()
    
    # Exit with appropriate code
    exit(0 if is_valid else 1)
