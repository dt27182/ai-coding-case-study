"""
Results Analysis Script
Analyzes log files and generates 2D grid metrics in CSV format.
"""

import os
import json
import argparse
import csv
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple


def parse_log_files(log_dir: Path) -> List[Dict]:
    """
    Parse all JSON log files in the directory.
    
    Args:
        log_dir: Directory containing log files
        
    Returns:
        List of parsed log data dicts
    """
    logs = []
    
    for log_file in log_dir.glob("*.json"):
        try:
            with open(log_file, 'r') as f:
                log_data = json.load(f)
                logs.append(log_data)
        except Exception as e:
            print(f"Warning: Could not parse {log_file}: {e}")
    
    return logs


def aggregate_results(logs: List[Dict], model_filter: str = None) -> Dict:
    """
    Aggregate results into 2D grids.
    
    Args:
        logs: List of log data dicts
        model_filter: Optional model name to filter by
        
    Returns:
        Dict containing aggregated data:
            - correct_grid: (num_people, num_categories) -> count
            - total_grid: (num_people, num_categories) -> count
            - error_grid: (num_people, num_categories) -> count
            - people_values: sorted list of people counts
            - category_values: sorted list of category counts
    """
    correct_grid = defaultdict(int)
    total_grid = defaultdict(int)
    error_grid = defaultdict(int)
    
    people_set = set()
    category_set = set()
    
    for log in logs:
        # Filter by model if specified
        if model_filter and log.get('model') != model_filter:
            continue
        
        num_people = log.get('num_people')
        num_categories = log.get('num_categories')
        
        if num_people is None or num_categories is None:
            continue
        
        people_set.add(num_people)
        category_set.add(num_categories)
        
        key = (num_people, num_categories)
        
        # Count total
        total_grid[key] += 1
        
        # Count correct
        if log.get('correct', False):
            correct_grid[key] += 1
        
        # Count errors
        if log.get('status') == 'error':
            error_grid[key] += 1
    
    return {
        'correct_grid': correct_grid,
        'total_grid': total_grid,
        'error_grid': error_grid,
        'people_values': sorted(people_set),
        'category_values': sorted(category_set)
    }


def generate_csv_report(
    aggregated_data: Dict,
    output_file: Path,
    model_name: str = "all"
):
    """
    Generate a CSV file with all 2D grids.
    
    Args:
        aggregated_data: Aggregated data from aggregate_results()
        output_file: Path to output CSV file
        model_name: Name of model for the report header
    """
    people_values = aggregated_data['people_values']
    category_values = aggregated_data['category_values']
    correct_grid = aggregated_data['correct_grid']
    total_grid = aggregated_data['total_grid']
    error_grid = aggregated_data['error_grid']
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Write header
        writer.writerow([f"Logic Puzzle Evaluation Results - Model: {model_name}"])
        writer.writerow([])
        
        # Section 1: Correct Count Grid
        writer.writerow(["Correct Count Grid"])
        writer.writerow(["(Rows = Number of People, Columns = Number of Categories)"])
        
        # Header row with category values
        header = ["People \\ Categories"] + [str(c) for c in category_values]
        writer.writerow(header)
        
        # Data rows
        for p in people_values:
            row = [str(p)]
            for c in category_values:
                count = correct_grid.get((p, c), 0)
                row.append(str(count))
            writer.writerow(row)
        
        writer.writerow([])
        
        # Section 2: Total Count Grid
        writer.writerow(["Total Count Grid"])
        writer.writerow(["(Rows = Number of People, Columns = Number of Categories)"])
        
        # Header row
        writer.writerow(header)
        
        # Data rows
        for p in people_values:
            row = [str(p)]
            for c in category_values:
                count = total_grid.get((p, c), 0)
                row.append(str(count))
            writer.writerow(row)
        
        writer.writerow([])
        
        # Section 3: Pass Rate Grid
        writer.writerow(["Pass Rate Grid (Correct / Total)"])
        writer.writerow(["(Rows = Number of People, Columns = Number of Categories)"])
        
        # Header row
        writer.writerow(header)
        
        # Data rows
        for p in people_values:
            row = [str(p)]
            for c in category_values:
                correct = correct_grid.get((p, c), 0)
                total = total_grid.get((p, c), 0)
                if total > 0:
                    pass_rate = correct / total
                    row.append(f"{pass_rate:.4f}")
                else:
                    row.append("N/A")
            writer.writerow(row)
        
        writer.writerow([])
        
        # Section 4: Error Count Grid
        writer.writerow(["Error Count Grid"])
        writer.writerow(["(Rows = Number of People, Columns = Number of Categories)"])
        
        # Header row
        writer.writerow(header)
        
        # Data rows
        for p in people_values:
            row = [str(p)]
            for c in category_values:
                count = error_grid.get((p, c), 0)
                row.append(str(count))
            writer.writerow(row)


def main():
    """Main entry point for analysis script."""
    parser = argparse.ArgumentParser(
        description='Analyze logic puzzle evaluation results'
    )
    parser.add_argument(
        '--log-dir',
        type=str,
        required=True,
        help='Directory containing log files'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='analysis_results.csv',
        help='Output CSV file (default: analysis_results.csv)'
    )
    parser.add_argument(
        '--model',
        type=str,
        default=None,
        help='Filter by specific model (optional)'
    )
    
    args = parser.parse_args()
    
    log_dir = Path(args.log_dir)
    
    if not log_dir.exists() or not log_dir.is_dir():
        print(f"ERROR: Log directory does not exist: {log_dir}")
        return 1
    
    # Parse log files
    print(f"Parsing log files from: {log_dir}")
    logs = parse_log_files(log_dir)
    
    if not logs:
        print("ERROR: No valid log files found")
        return 1
    
    print(f"Found {len(logs)} log files")
    
    # Check if we need to generate reports for each model separately
    models = set(log.get('model') for log in logs if log.get('model'))
    
    if args.model:
        # Single model report
        print(f"Filtering for model: {args.model}")
        aggregated = aggregate_results(logs, model_filter=args.model)
        
        output_file = Path(args.output)
        print(f"Generating CSV report: {output_file}")
        generate_csv_report(aggregated, output_file, model_name=args.model)
        print(f"Analysis complete! Results saved to: {output_file}")
        
    else:
        # Generate reports for all models combined and separately
        
        # Combined report
        print("Generating combined report for all models...")
        aggregated_all = aggregate_results(logs)
        output_file_all = Path(args.output)
        generate_csv_report(aggregated_all, output_file_all, model_name="all")
        print(f"Combined report saved to: {output_file_all}")
        
        # Individual model reports
        output_base = Path(args.output).stem
        output_ext = Path(args.output).suffix
        output_dir = Path(args.output).parent
        
        for model in models:
            print(f"\nGenerating report for model: {model}")
            aggregated = aggregate_results(logs, model_filter=model)
            
            # Create safe filename
            model_safe = model.replace('/', '_').replace(':', '_')
            output_file = output_dir / f"{output_base}_{model_safe}{output_ext}"
            
            generate_csv_report(aggregated, output_file, model_name=model)
            print(f"Model report saved to: {output_file}")
        
        print("\n" + "="*80)
        print("Analysis complete!")
        print(f"Combined report: {output_file_all}")
        print(f"Individual model reports: {output_dir / (output_base + '_*' + output_ext)}")
        print("="*80)
    
    return 0


if __name__ == "__main__":
    exit(main())
