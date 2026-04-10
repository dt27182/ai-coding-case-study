import pytest
from themes import THEMES

def test_themes_count_and_uniqueness():
    # Verify there are exactly 20 categories
    assert len(THEMES) == 20, f"Expected 20 categories, but found {len(THEMES)}"
    
    for category, values in THEMES.items():
        # Verify 20 values per category
        assert len(values) == 20, f"Expected 20 values in category '{category}', but found {len(values)}"
        
        # Verify all values in the category are unique
        unique_values = set(values)
        assert len(unique_values) == 20, f"Values in category '{category}' are not all unique. Expected 20 unique values, found {len(unique_values)}."
