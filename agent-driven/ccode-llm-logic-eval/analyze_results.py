#!/usr/bin/env python3
"""Analyze puzzle evaluation results and generate statistics grids."""

import argparse
import json
import csv
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, Tuple


def load_results(directory: Path) -> list:
    """Load all JSON result files from a directory."""
    results = []
    json_files = list(directory.glob("**/*.json"))

    for json_file in json_files:
        try:
            with open(json_file) as f:
                data = json.load(f)
                results.append(data)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Failed to load {json_file}: {e}", file=sys.stderr)

    return results


def analyze_results(results: list) -> Dict[Tuple[int, int], Dict[str, int]]:
    """Analyze results and return counts by (num_people, num_attributes).

    Returns:
        Dictionary mapping (num_people, num_attributes) to counts dict with:
        - total: total number of runs
        - correct: number of correct (match=True) runs
        - errors: number of error runs
    """
    stats = defaultdict(lambda: {"total": 0, "correct": 0, "errors": 0})

    for result in results:
        # Extract puzzle configuration
        puzzle = result.get("puzzle", {})
        num_people = puzzle.get("num_people", 0)
        num_attributes = len(puzzle.get("attributes", {}))

        if num_people == 0 or num_attributes == 0:
            continue

        key = (num_people, num_attributes)
        stats[key]["total"] += 1

        # Check if correct
        if result.get("match", False):
            stats[key]["correct"] += 1

        # Check if error
        if result.get("error"):
            stats[key]["errors"] += 1

    return dict(stats)


def get_grid_dimensions(stats: Dict[Tuple[int, int], Dict[str, int]]) -> Tuple[list, list]:
    """Get sorted lists of unique people counts and attribute counts."""
    people_set = set()
    attrs_set = set()

    for (num_people, num_attrs) in stats.keys():
        people_set.add(num_people)
        attrs_set.add(num_attrs)

    return sorted(people_set), sorted(attrs_set)


def write_csv(stats: Dict[Tuple[int, int], Dict[str, int]], output_file: Path):
    """Write all grids to a single CSV file."""
    people_list, attrs_list = get_grid_dimensions(stats)

    if not people_list or not attrs_list:
        print("No data to analyze", file=sys.stderr)
        return

    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)

        # Header row for attributes
        header = ["People \\ Attributes"] + [str(a) for a in attrs_list]

        # Grid 1: Correct counts
        writer.writerow(["=== CORRECT COUNTS ==="])
        writer.writerow(header)
        for num_people in people_list:
            row = [str(num_people)]
            for num_attrs in attrs_list:
                count = stats.get((num_people, num_attrs), {}).get("correct", 0)
                row.append(str(count))
            writer.writerow(row)
        writer.writerow([])  # Empty row separator

        # Grid 2: Total counts
        writer.writerow(["=== TOTAL COUNTS ==="])
        writer.writerow(header)
        for num_people in people_list:
            row = [str(num_people)]
            for num_attrs in attrs_list:
                count = stats.get((num_people, num_attrs), {}).get("total", 0)
                row.append(str(count))
            writer.writerow(row)
        writer.writerow([])  # Empty row separator

        # Grid 3: Pass rates
        writer.writerow(["=== PASS RATES ==="])
        writer.writerow(header)
        for num_people in people_list:
            row = [str(num_people)]
            for num_attrs in attrs_list:
                data = stats.get((num_people, num_attrs), {})
                total = data.get("total", 0)
                correct = data.get("correct", 0)
                if total > 0:
                    rate = correct / total
                    row.append(f"{rate:.2%}")
                else:
                    row.append("N/A")
            writer.writerow(row)
        writer.writerow([])  # Empty row separator

        # Grid 4: Error counts
        writer.writerow(["=== ERROR COUNTS ==="])
        writer.writerow(header)
        for num_people in people_list:
            row = [str(num_people)]
            for num_attrs in attrs_list:
                count = stats.get((num_people, num_attrs), {}).get("errors", 0)
                row.append(str(count))
            writer.writerow(row)

    print(f"Analysis written to {output_file}")


def print_summary(stats: Dict[Tuple[int, int], Dict[str, int]]):
    """Print a text summary to console."""
    total_runs = sum(s["total"] for s in stats.values())
    total_correct = sum(s["correct"] for s in stats.values())
    total_errors = sum(s["errors"] for s in stats.values())

    print(f"\nSummary:")
    print(f"  Total runs: {total_runs}")
    print(f"  Correct: {total_correct}")
    print(f"  Errors: {total_errors}")
    if total_runs > 0:
        print(f"  Overall pass rate: {total_correct / total_runs:.2%}")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze puzzle evaluation results and generate statistics"
    )
    parser.add_argument(
        "directory",
        type=Path,
        help="Directory containing JSON result files"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=Path("analysis.csv"),
        help="Output CSV file (default: analysis.csv)"
    )

    args = parser.parse_args()

    if not args.directory.exists():
        print(f"Error: Directory {args.directory} does not exist", file=sys.stderr)
        sys.exit(1)

    print(f"Loading results from {args.directory}...")
    results = load_results(args.directory)
    print(f"Loaded {len(results)} result files")

    if not results:
        print("No results found", file=sys.stderr)
        sys.exit(1)

    stats = analyze_results(results)
    write_csv(stats, args.output)
    print_summary(stats)


if __name__ == "__main__":
    main()
