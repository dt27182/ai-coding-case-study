#!/usr/bin/env python3
"""Validate attribute pools for completeness and uniqueness."""

from attribute_pools import PERSON_NAMES, ATTRIBUTE_POOLS

def validate_pools():
    """Validate all attribute pools."""
    errors = []
    warnings = []

    print("Validating attribute pools...")
    print("=" * 60)

    # Check PERSON_NAMES
    print(f"\nPERSON_NAMES: {len(PERSON_NAMES)} values")
    if len(PERSON_NAMES) < 20:
        errors.append(f"PERSON_NAMES has only {len(PERSON_NAMES)} values (need 20)")
    duplicates = find_duplicates(PERSON_NAMES)
    if duplicates:
        errors.append(f"PERSON_NAMES has duplicates: {duplicates}")
    else:
        print("  ✓ No duplicates")

    # Check each attribute pool
    print(f"\nATTRIBUTE_POOLS: {len(ATTRIBUTE_POOLS)} categories")

    for attr_name, values in ATTRIBUTE_POOLS.items():
        print(f"\n  {attr_name}: {len(values)} values")

        # Check count
        if len(values) < 20:
            errors.append(f"{attr_name} has only {len(values)} values (need 20)")

        # Check duplicates
        duplicates = find_duplicates(values)
        if duplicates:
            errors.append(f"{attr_name} has duplicates: {duplicates}")
        else:
            print(f"    ✓ No duplicates")

    # Summary
    print("\n" + "=" * 60)

    if errors:
        print(f"\n❌ VALIDATION FAILED with {len(errors)} error(s):\n")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print(f"\n✓ All {len(ATTRIBUTE_POOLS) + 1} pools validated successfully!")
        print(f"  - PERSON_NAMES: {len(PERSON_NAMES)} unique values")
        print(f"  - {len(ATTRIBUTE_POOLS)} attribute categories, each with 20+ unique values")
        print(f"  - System supports up to 20x20 puzzles")
        return True


def find_duplicates(values):
    """Find duplicate values in a list."""
    seen = set()
    duplicates = []
    for v in values:
        if v in seen:
            duplicates.append(v)
        seen.add(v)
    return duplicates


if __name__ == "__main__":
    import sys
    success = validate_pools()
    sys.exit(0 if success else 1)
