import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from attribute_pools import ATTRIBUTE_POOLS

REQUIRED_ATTRIBUTES = 20
REQUIRED_VALUES = 20

passed = True

if len(ATTRIBUTE_POOLS) != REQUIRED_ATTRIBUTES:
    print(f"FAIL: expected {REQUIRED_ATTRIBUTES} attributes, got {len(ATTRIBUTE_POOLS)}")
    passed = False
else:
    print(f"PASS: {REQUIRED_ATTRIBUTES} attributes found")

for name, values in ATTRIBUTE_POOLS.items():
    if len(values) != REQUIRED_VALUES:
        print(f"FAIL: '{name}' has {len(values)} values (expected {REQUIRED_VALUES})")
        passed = False

    dupes = {v for v in values if values.count(v) > 1}
    if dupes:
        print(f"FAIL: '{name}' has duplicate values: {dupes}")
        passed = False

if passed:
    print(f"PASS: all attributes have {REQUIRED_VALUES} unique values")
