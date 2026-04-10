import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from execute_tests import _compare_solutions

expected = [
    {"Position": 0, "Name": "Alice", "Job": "Doctor"},
    {"Position": 1, "Name": "Bob",   "Job": "Farmer"},
]

def test_correct_solution():
    llm = [
        {"Position": 0, "Name": "Alice", "Job": "Doctor"},
        {"Position": 1, "Name": "Bob",   "Job": "Farmer"},
    ]
    assert _compare_solutions(expected, llm) == []

def test_wrong_solution():
    llm = [
        {"Position": 0, "Name": "Bob",   "Job": "Doctor"},
        {"Position": 1, "Name": "Alice", "Job": "Farmer"},
    ]
    mismatches = _compare_solutions(expected, llm)
    assert "  Position 0, Name: expected 'Alice', got 'Bob'" in mismatches
    assert "  Position 1, Name: expected 'Bob', got 'Alice'" in mismatches

test_correct_solution()
print("PASS: test_correct_solution")

test_wrong_solution()
print("PASS: test_wrong_solution")
