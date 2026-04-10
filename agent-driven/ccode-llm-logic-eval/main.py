#!/usr/bin/env python3
"""Main orchestrator for logic puzzle LLM evaluation system."""

import argparse
import json
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Tuple, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from puzzle_generator import generate_puzzle
from openrouter_client import OpenRouterClient, format_prompt
from comparator import evaluate_response
from utils import (
    setup_logging,
    create_result_directory,
    get_timestamp,
    save_json,
    load_env,
    get_api_key
)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Evaluate LLMs on logic grid puzzles via OpenRouter"
    )

    parser.add_argument(
        "-p", "--min-people",
        type=int,
        default=3,
        help="Minimum number of people (positions) in puzzles"
    )

    parser.add_argument(
        "-P", "--max-people",
        type=int,
        default=3,
        help="Maximum number of people (positions) in puzzles"
    )

    parser.add_argument(
        "-i", "--min-items",
        type=int,
        default=3,
        help="Minimum number of attributes per person (excluding name)"
    )

    parser.add_argument(
        "-I", "--max-items",
        type=int,
        default=3,
        help="Maximum number of attributes per person (excluding name)"
    )

    parser.add_argument(
        "-m", "--models",
        type=str,
        default='tngtech/deepseek-r1t2-chimera:free',
        help="Comma-separated list of OpenRouter model IDs"
    )

    parser.add_argument(
        "-n", "--puzzles-per-config",
        type=int,
        default=1,
        help="Number of puzzle instances per configuration"
    )

    parser.add_argument(
        "-c", "--concurrency",
        type=int,
        default=300,
        help="Maximum concurrent API requests"
    )

    args = parser.parse_args()

    # Validation
    if args.min_people < 1 or args.max_people < args.min_people:
        parser.error("Invalid people range")

    if args.min_items < 1 or args.max_items < args.min_items:
        parser.error("Invalid items range")

    if args.puzzles_per_config < 1:
        parser.error("puzzles-per-config must be at least 1")

    if args.concurrency < 1:
        parser.error("concurrency must be at least 1")

    return args


def generate_configurations(
    min_people: int,
    max_people: int,
    min_items: int,
    max_items: int
) -> List[Tuple[int, int]]:
    """Generate all (num_people, num_items) configurations."""
    configs = []
    for num_people in range(min_people, max_people + 1):
        for num_items in range(min_items, max_items + 1):
            configs.append((num_people, num_items))
    return configs


def evaluate_single_model(task_info: Dict[str, Any], api_key: str) -> Dict[str, Any]:
    """Evaluate a single model on a single puzzle.

    Args:
        task_info: Dictionary containing puzzle, model, and metadata
        api_key: OpenRouter API key

    Returns:
        Dictionary with status and any error information
    """
    model = task_info["model"]
    puzzle = task_info["puzzle"]
    config_str = task_info["config_str"]
    puzzle_idx = task_info["puzzle_idx"]
    base_name = task_info["base_name"]
    num_people = task_info["num_people"]
    total_attributes = task_info["total_attributes"]

    # Create result directory and logger for this task
    result_dir = create_result_directory(model)
    json_path = result_dir / f"{base_name}.json"
    log_path = result_dir / f"{base_name}.log"
    logger = setup_logging(log_path, logger_name=str(log_path))

    logger.info("=" * 70)
    logger.info(f"Evaluating {model} on puzzle {puzzle_idx}")
    logger.info(f"Configuration: {num_people} people, {total_attributes} attributes")
    logger.info("=" * 70)
    logger.debug("Puzzle:\n" + json.dumps(puzzle, indent=2))

    try:
        # Create OpenRouter client
        client = OpenRouterClient(api_key, logger)

        # Format prompt
        prompt = format_prompt(puzzle)
        logger.debug(f"Prompt:\n{prompt}")

        # Query model
        logger.info(f"Querying model: {model}")
        llm_response, api_info = client.query_model(model, prompt)

        if llm_response is None:
            logger.error("Failed to get response from model")

            # Save error result
            result = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "model": model,
                "puzzle": {
                    "num_people": puzzle["num_people"],
                    "attributes": puzzle["attributes"],
                    "clues": puzzle["clues"]
                },
                "actual_solution": puzzle["solution"],
                "llm_solution": None,
                "match": False,
                "differences": [],
                "error": f"API error: {api_info.get('error', 'Unknown error')}",
                "response_time_ms": api_info.get("response_time_ms"),
                "tokens_used": api_info.get("tokens_used")
            }
            save_json(result, json_path)
            print(f"  [{model}] {config_str} puzzle {puzzle_idx}: ERROR ({api_info.get('error', 'Unknown')})")
            return {"status": "ERROR", "model": model, "error": api_info.get("error")}

        logger.debug(f"Raw response:\n{llm_response}")

        # Evaluate response
        logger.info("Parsing and evaluating response")
        eval_result = evaluate_response(llm_response, puzzle["solution"])

        # Determine status
        if eval_result["parsing_error"]:
            status = "PARSE_ERROR"
            logger.error(f"Parsing error: {eval_result['parsing_error']}")
        elif eval_result["evaluation"]["exact_match"]:
            status = "MATCH"
            logger.info("Solution matches!")
        else:
            status = "FAIL"
            logger.warning(f"Solution mismatch: {eval_result['evaluation']['differences']}")

        # Build result document
        error_msg = None
        if eval_result["parsing_error"]:
            error_msg = f"Parsing error: {eval_result['parsing_error']}"

        result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "model": model,
            "puzzle": {
                "num_people": puzzle["num_people"],
                "attributes": puzzle["attributes"],
                "clues": puzzle["clues"]
            },
            "actual_solution": puzzle["solution"],
            "llm_solution": eval_result["parsed_solution"],
            "match": eval_result.get("evaluation", {}).get("exact_match", False),
            "differences": eval_result.get("evaluation", {}).get("differences", []),
            "error": error_msg,
            "response_time_ms": api_info["response_time_ms"],
            "tokens_used": api_info.get("tokens_used")
        }

        # Save result
        save_json(result, json_path)
        logger.info(f"Result saved to {json_path}")

        # Print progress
        print(f"  [{model}] {config_str} puzzle {puzzle_idx}: {status} ({api_info['response_time_ms']}ms)")

        return {"status": status, "model": model}

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"  [{model}] {config_str} puzzle {puzzle_idx}: ERROR ({e})")
        return {"status": "ERROR", "model": model, "error": str(e)}


def main():
    """Main execution flow."""
    # Load environment variables
    load_env()

    # Parse arguments
    args = parse_args()

    # Get API key
    api_key = get_api_key()

    # Parse model list
    models = [m.strip() for m in args.models.split(",")]

    # Generate configurations
    configs = generate_configurations(
        args.min_people,
        args.max_people,
        args.min_items,
        args.max_items
    )

    # Print summary
    total_evaluations = len(configs) * args.puzzles_per_config * len(models)
    print("=" * 70)
    print("Logic Puzzle LLM Evaluation System")
    print("=" * 70)
    print(f"Configurations: {len(configs)}")
    print(f"Puzzles per config: {args.puzzles_per_config}")
    print(f"Models: {len(models)}")
    print(f"Total evaluations: {total_evaluations}")
    print(f"Concurrency: {args.concurrency}")
    print(f"Models to evaluate: {', '.join(models)}")
    print("=" * 70)
    print()

    start_time = time.time()

    # Generate all puzzles and collect tasks
    print("Generating puzzles...")
    tasks = []
    for num_people, num_items in configs:
        total_attributes = num_items + 1
        config_str = f"{num_people}x{num_items}"

        for puzzle_idx in range(args.puzzles_per_config):
            timestamp = get_timestamp()
            base_name = f"{timestamp}_{config_str}_puzzle_{puzzle_idx}"

            # Generate puzzle
            try:
                puzzle = generate_puzzle(num_people, total_attributes)
            except Exception as e:
                print(f"  ERROR: Failed to generate puzzle {config_str} #{puzzle_idx}: {e}")
                continue

            # Create task for each model
            for model in models:
                tasks.append({
                    "model": model,
                    "puzzle": puzzle,
                    "config_str": config_str,
                    "puzzle_idx": puzzle_idx,
                    "base_name": base_name,
                    "num_people": num_people,
                    "total_attributes": total_attributes
                })

    print(f"Generated {len(tasks)} evaluation tasks")
    print("=" * 70)
    print()

    # Execute tasks in parallel
    print(f"Evaluating with {args.concurrency} concurrent workers...")
    print("-" * 70)

    completed = 0
    with ThreadPoolExecutor(max_workers=args.concurrency) as executor:
        futures = [executor.submit(evaluate_single_model, task, api_key) for task in tasks]

        for future in as_completed(futures):
            completed += 1
            try:
                future.result()
            except Exception as e:
                print(f"  Task failed: {e}")

    # Print final summary
    elapsed_time = time.time() - start_time
    print()
    print("=" * 70)
    print("Completed")
    print("=" * 70)
    print(f"Total tasks: {len(tasks)}")
    print(f"Completed: {completed}")
    print(f"Time elapsed: {elapsed_time:.1f}s")
    print(f"Results saved to results/ directory")
    print("=" * 70)


if __name__ == "__main__":
    main()
