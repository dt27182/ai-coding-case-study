from attribute_pool import ATTRIBUTE_POOL


def test_attribute_pool():
    print("Testing ATTRIBUTE_POOL...")
    print("=" * 80)
    
    num_attributes = len(ATTRIBUTE_POOL)
    print(f"1. Number of attributes: {num_attributes}")
    assert num_attributes == 21, f"Expected 21 attributes, got {num_attributes}"
    print("   ✓ PASS: 21 attributes found")
    print()
    
    print("2. Checking each attribute has 21 values:")
    all_have_20_values = True
    for attr_name, values in ATTRIBUTE_POOL.items():
        num_values = len(values)
        if num_values != 20:
            print(f"   ✗ FAIL: {attr_name} has {num_values} values, expected 20")
            all_have_20_values = False
        else:
            print(f"   ✓ {attr_name}: {num_values} values")
    
    assert all_have_20_values, "Not all attributes have 20 values"
    print("   ✓ PASS: All attributes have 20 values")
    print()
    
    print("3. Checking each attribute has unique values (no duplicates):")
    all_unique = True
    for attr_name, values in ATTRIBUTE_POOL.items():
        unique_values = set(values)
        if len(unique_values) != len(values):
            duplicates = len(values) - len(unique_values)
            print(f"   ✗ FAIL: {attr_name} has {duplicates} duplicate(s)")
            all_unique = False
        else:
            print(f"   ✓ {attr_name}: all values unique")
    
    assert all_unique, "Some attributes have duplicate values"
    print("   ✓ PASS: All attributes have unique values")
    print()
    
    print("=" * 80)
    print("ALL TESTS PASSED ✓")


if __name__ == '__main__':
    test_attribute_pool()
