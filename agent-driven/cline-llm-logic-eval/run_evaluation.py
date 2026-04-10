"""
Main Evaluation Runner
Generates puzzles, tests them with LLMs, and logs results.
"""

import os
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import List
import traceback

from puzzle_generator import generate_puzzle
from llm_tester import LLMTester, compare_solutions


def create_log_filename(num_people: int, num_categories: int, model: str, timestamp: str) -> str:
    """
    Create a standardized log filename.
    
    Args:
        num_people: Number of people in puzzle
        num_categories: Number of categories in puzzle
        model: Model identifier
        timestamp: Timestamp string
        
    Returns:
        Filename string
    """
    # Sanitize model name for filename
    model_safe = model.replace('/', '_').replace(':', '_')
    return f"p{num_people}_c{num_categories}_{model_safe}_{timestamp}.json"


def run_single_evaluation(
    num_people: int,
    num_categories: int,
    model: str,
    tester: LLMTester,
    output_dir: Path,
    timestamp: str,
    seed: int = None
) -> dict:
    """
    Run a single puzzle evaluation: generate, test, compare, and log.
    
    Args:
        num_people: Number of people for puzzle
        num_categories: Number of categories for puzzle
        model: LLM model to test
        tester: LLMTester instance
        output_dir: Directory to save logs
        timestamp: Timestamp for filenames
        seed: Random seed (optional)
        
    Returns:
        Summary dict with results
    """
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'num_people': num_people,
        'num_categories': num_categories,
        'model': model,
        'status': 'started'
    }
    
    try:
        # Generate puzzle
        print(f"  Generating puzzle (people={num_people}, categories={num_categories})...")
        puzzle = generate_puzzle(num_people, num_categories, seed=seed)
        
        log_data['puzzle_prompt'] = puzzle.get_prompt()
        log_data['expected_solution'] = puzzle.get_solution_json()
        
        # Test with LLM
        print(f"  Testing with {model}...")
        result = tester.test_puzzle(puzzle.get_prompt(), model)
        
        log_data['llm_response'] = result
        
        if not result['success']:
            log_data['status'] = 'error'
            log_data['error'] = result.get('error', 'Unknown error')
            log_data['correct'] = False
        else:
            log_data['parsed_llm_solution'] = result.get('parsed_solution')
            
            # Compare solutions
            comparison = compare_solutions(
                puzzle.get_solution_json(),
                result.get('parsed_solution')
            )
            
            log_data['comparison'] = comparison
            log_data['correct'] = comparison['correct']
            log_data['status'] = 'completed'
        
    except Exception as e:
        log_data['status'] = 'error'
        log_data['error'] = str(e)
        log_data['traceback'] = traceback.format_exc()
        log_data['correct'] = False
        print(f"  ERROR: {e}")
    
    # Write log file
    log_filename = create_log_filename(num_people, num_categories, model, timestamp)
    log_path = output_dir / log_filename
    
    with open(log_path, 'w') as f:
        json.dump(log_data, f, indent=2)
    
    print(f"  Result: {'CORRECT' if log_data.get('correct') else 'INCORRECT/ERROR'}")
    print(f"  Log saved to: {log_filename}")
    
    return {
        'num_people': num_people,
        'num_categories': num_categories,
        'model': model,
        'correct': log_data.get('correct', False),
        'status': log_data['status']
    }


def main():
    """Main entry point for evaluation runner."""
    parser = argparse.ArgumentParser(
        description='Run logic puzzle evaluation on LLMs via OpenRouter'
    )
    parser.add_argument(
        '--min-people',
        type=int,
        required=True,
        help='Minimum number of people (1-20)'
    )
    parser.add_argument(
        '--max-people',
        type=int,
        required=True,
        help='Maximum number of people (1-20)'
    )
    parser.add_argument(
        '--min-categories',
        type=int,
        required=True,
        help='Minimum number of categories (1-20)'
    )
    parser.add_argument(
        '--max-categories',
        type=int,
        required=True,
        help='Maximum number of categories (1-20)'
    )
    parser.add_argument(
        '--models',
        nargs='+',
        required=True,
        help='List of model identifiers to test (e.g., anthropic/claude-3-opus)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='logs',
        help='Directory to save log files (default: logs)'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=None,
        help='Random seed for reproducibility (optional)'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not (1 <= args.min_people <= 20 and 1 <= args.max_people <= 20):
        print("ERROR: min-people and max-people must be between 1 and 20")
        return 1
    
    if not (1 <= args.min_categories <= 20 and 1 <= args.max_categories <= 20):
        print("ERROR: min-categories and max-categories must be between 1 and 20")
        return 1
    
    if args.min_people > args.max_people:
        print("ERROR: min-people must be <= max-people")
        return 1
    
    if args.min_categories > args.max_categories:
        print("ERROR: min-categories must be <= max-categories")
        return 1
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize LLM tester
    try:
        tester = LLMTester()
    except ValueError as e:
        print(f"ERROR: {e}")
        return 1
    
    # Generate timestamp for this run
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Calculate total number of evaluations
    num_people_range = args.max_people - args.min_people + 1
    num_categories_range = args.max_categories - args.min_categories + 1
    num_models = len(args.models)
    total_evaluations = num_people_range * num_categories_range * num_models
    
    print("="*80)
    print("Logic Puzzle LLM Evaluation")
    print("="*80)
    print(f"People range: {args.min_people} to {args.max_people}")
    print(f"Categories range: {args.min_categories} to {args.max_categories}")
    print(f"Models: {', '.join(args.models)}")
    print(f"Total evaluations: {total_evaluations}")
    print(f"Output directory: {output_dir.absolute()}")
    print(f"Timestamp: {timestamp}")
    print("="*80)
    print()
    
    # Run evaluations
    results = []
    current = 0
    
    for num_people in range(args.min_people, args.max_people + 1):
        for num_categories in range(args.min_categories, args.max_categories + 1):
            for model in args.models:
                current += 1
                print(f"[{current}/{total_evaluations}] Testing: people={num_people}, categories={num_categories}, model={model}")
                
                result = run_single_evaluation(
                    num_people=num_people,
                    num_categories=num_categories,
                    model=model,
                    tester=tester,
                    output_dir=output_dir,
                    timestamp=timestamp,
                    seed=args.seed
                )
                
                results.append(result)
                print()
    
    # Print summary
    print("="*80)
    print("EVALUATION COMPLETE")
    print("="*80)
    
    correct_count = sum(1 for r in results if r['correct'])
    error_count = sum(1 for r in results if r['status'] == 'error')
    
    print(f"Total evaluations: {len(results)}")
    print(f"Correct: {correct_count}")
    print(f"Incorrect: {len(results) - correct_count - error_count}")
    print(f"Errors: {error_count}")
    print(f"Accuracy: {correct_count / len(results) * 100:.1f}%")
    print()
    print(f"All logs saved to: {output_dir.absolute()}")
    print()
    print("To analyze results, run:")
    print(f"  python analyze_results.py --log-dir {args.output_dir}")
    print("="*80)
    
    return 0


if __name__ == "__main__":
    exit(main())
