#!/usr/bin/env python3
"""
Analyze puzzle evaluation results from log files.

This script processes log files from LLM puzzle evaluations and generates
statistical grids showing performance across different puzzle configurations.
"""

import os
import re
import argparse
from collections import defaultdict


def parse_log_file(filepath):
    """
    Parse a single log file and extract relevant information.
    
    Returns:
        dict: Contains 'num_people', 'num_attributes', 'correct', 'errored'
              Returns None if parsing fails
    """
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Extract num_people and num_attributes from CONFIGURATION section
        config_match = re.search(r'People: (\d+), Attributes: (\d+)', content)
        if not config_match:
            return None
        
        num_people = int(config_match.group(1))
        num_attributes = int(config_match.group(2))
        
        # Check if there was an exception or error
        # First check for the explicit Errored flag in METADATA
        errored_match = re.search(r'Errored: (True|False)', content)
        if errored_match:
            errored = errored_match.group(1) == 'True'
        
        # Extract correctness from EVALUATION section
        correct = False
        if not errored:
            eval_match = re.search(r'Correct: (True|False)', content)
            if eval_match:
                correct = eval_match.group(1) == 'True'
        
        return {
            'num_people': num_people,
            'num_attributes': num_attributes,
            'correct': correct,
            'errored': errored
        }
    
    except Exception as e:
        print(f"Warning: Failed to parse {filepath}: {e}")
        return None


def collect_results(results_dir):
    """
    Recursively collect results from all log files in the directory.
    
    Returns:
        list: List of parsed result dictionaries
    """
    results = []
    
    for root, dirs, files in os.walk(results_dir):
        for filename in files:
            if filename.endswith('.txt') and filename.startswith('puzzle_'):
                filepath = os.path.join(root, filename)
                parsed = parse_log_file(filepath)
                if parsed:
                    results.append(parsed)
    
    return results


def build_grids(results):
    """
    Build 2D grids for various statistics.
    
    Returns:
        tuple: (correct_grid, total_grid, pass_rate_grid, error_grid, people_range, attr_range)
    """
    correct_grid = defaultdict(lambda: defaultdict(int))
    total_grid = defaultdict(lambda: defaultdict(int))
    error_grid = defaultdict(lambda: defaultdict(int))
    
    for result in results:
        num_people = result['num_people']
        num_attributes = result['num_attributes']
        
        total_grid[num_people][num_attributes] += 1
        
        if result['errored']:
            error_grid[num_people][num_attributes] += 1
        elif result['correct']:
            correct_grid[num_people][num_attributes] += 1
    
    # Determine ranges
    all_people = set()
    all_attributes = set()
    for result in results:
        all_people.add(result['num_people'])
        all_attributes.add(result['num_attributes'])
    
    people_range = sorted(all_people) if all_people else []
    attr_range = sorted(all_attributes) if all_attributes else []
    
    # Build pass rates grid
    pass_rate_grid = defaultdict(lambda: defaultdict(str))
    for people in people_range:
        for attr in attr_range:
            total = total_grid[people][attr]
            correct = correct_grid[people][attr]
            if total > 0:
                pass_rate = (correct / total) * 100
                pass_rate_grid[people][attr] = f"{pass_rate:.1f}%"
            else:
                pass_rate_grid[people][attr] = "N/A"
    
    return correct_grid, total_grid, pass_rate_grid, error_grid, people_range, attr_range


def print_grid(grid, people_range, attr_range, title):
    """Print a 2D grid in a formatted table."""
    print(f"\n{title}")
    print("=" * (len(title) + 20))
    
    if not people_range or not attr_range:
        print("No data available")
        return
    
    # Header
    header = "People \\ Attributes"
    for attr in attr_range:
        header += f"\t{attr}"
    print(header)
    print("-" * (len(title) + 20))
    
    # Rows
    for people in people_range:
        row = f"{people}"
        for attr in attr_range:
            row += f"\t{grid[people][attr]}"
        print(row)


def generate_csv(correct_grid, total_grid, pass_rate_grid, error_grid, people_range, attr_range):
    """Generate CSV format with all 4 grids."""
    if not people_range or not attr_range:
        return "No data available"
    
    lines = []
    
    # Helper function to add a grid section
    def add_grid_section(title, grid):
        lines.append("")
        lines.append(title)
        header = "People \\ Attributes," + ",".join(str(attr) for attr in attr_range)
        lines.append(header)
        
        for people in people_range:
            row_values = [str(people)]
            for attr in attr_range:
                value = grid[people][attr]
                row_values.append(str(value))
            lines.append(",".join(row_values))
    
    # Add all 4 grids
    add_grid_section("1. Correct Runs Count", correct_grid)
    add_grid_section("2. Total Runs Count", total_grid)
    add_grid_section("3. Pass Rates (%)", pass_rate_grid)
    add_grid_section("4. Errored Runs Count", error_grid)
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze puzzle evaluation results from log files"
    )
    parser.add_argument(
        '-r', '--results_dir',
        help='Directory containing log files (will search recursively)'
    )
    parser.add_argument(
        '-o', '--output', default='results/results_analysis.csv',
        help='Output CSV file for pass rates (optional)'
    )
    
    args = parser.parse_args()
    
    
    print(f"Analyzing results in: {args.results_dir}")
    print("=" * 80)
    
    # Collect results
    results = collect_results(args.results_dir)
    
    print(f"Found {len(results)} puzzle runs\n")
    
    # Build grids
    correct_grid, total_grid, pass_rate_grid, error_grid, people_range, attr_range = build_grids(results)
    
    # Print grids
    print_grid(correct_grid, people_range, attr_range, 
               "1. Correct Runs Count")
    
    print_grid(total_grid, people_range, attr_range,
               "2. Total Runs Count")
    
    print_grid(pass_rate_grid, people_range, attr_range,
               "3. Pass Rates (%)")
    
    print_grid(error_grid, people_range, attr_range,
               "4. Errored Runs Count")
    
    # Generate CSV with all grids
    print("\nGenerating CSV output with all 4 grids...")
    csv_content = generate_csv(correct_grid, total_grid, pass_rate_grid, error_grid, people_range, attr_range)
    
    # Save CSV to file
    if args.output:
        with open(args.output, 'w') as f:
            f.write(csv_content)
        print(f"All grids saved to: {args.output}")
    else:
        print("\n" + "=" * 80)
        print("CSV Output (all 4 grids):")
        print("=" * 80)
        print(csv_content)
    
    print("\n" + "=" * 80)
    print("Analysis complete!")
    
    return 0


if __name__ == '__main__':
    exit(main())
