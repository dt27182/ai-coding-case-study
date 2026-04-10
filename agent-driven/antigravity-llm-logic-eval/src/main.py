import argparse
import json
import random

import time
import os
from dotenv import load_dotenv
from src.generator import LogicPuzzle
from src.client import query_model
from src.evaluator import verify_json

import concurrent.futures

import traceback

def get_log_filename(puzzle_counter, n, m, model):
    sanitized_model = model.replace("/", "_").replace(":", "_")
    log_dir = os.path.join("logs", sanitized_model)
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, f"puzzle_{puzzle_counter}_{n}_{m}.txt")

def evaluate_model(model, puzzle, puzzle_counter, n, m, dry_run):
    """
    Evaluates a single model on a single puzzle.
    Writes result to a model-specific CSV file.
    """
    # Calculate log filename upfront (needed for exception logging)
    log_filename = get_log_filename(puzzle_counter, n, m, model)
    
    try:
        # Generate clues specifically for this model's instance of the puzzle
        # This runs in parallel (though GIL limited for CPU, useful if mixed with I/O)
        print(f"Generating clues for {model} (Puzzle #{puzzle_counter})...")
        puzzle.generate_clues()
        prompt = puzzle.render_prompt()
        
        with open(log_filename, "w") as logkw:
            logkw.write(f"Model: {model}\n")
            logkw.write(f"Puzzle ID: {puzzle_counter}\n")
            logkw.write(f"Size: {n} people, {m} attributes\n")
            logkw.write("GROUND TRUTH:\n")
            logkw.write(json.dumps(puzzle.ground_truth, indent=2))
            logkw.write("\n" + "="*40 + "\n")
            logkw.write("PROMPT:\n")
            logkw.write(prompt)
            logkw.write("\n" + "="*40 + "\n")

        if dry_run:
            print(f"Dry Run: Skipping query for {model} (Sleeping 5s to verify parallelism)")
            time.sleep(5)
            print(f"Dry Run: Skipping query for {model} (Sleeping 5s to verify parallelism)")
            time.sleep(5)
            response_content = "Dry Run - No LLM Query"
            full_response = "Dry Run Object"
            is_correct = False
            status = "DryRun"
            duration = 5.0
        else:
            print(f"Querying {model}...")
            start_time = time.time()
            
            response = query_model(prompt, model)
            duration = time.time() - start_time
            full_response = json.dumps(response.model_dump(), indent=2)
            response_content = response.output_text
        
        # Log details to text file
        with open(log_filename, "a") as logkw:
            logkw.write("LLM RESPONSE FULL OBJECT:\n")
            logkw.write(full_response)
            logkw.write("\n" + "="*40 + "\n")
            logkw.write("LLM RESPONSE CONTENT:\n")
            logkw.write(response_content)
            logkw.write("\n")
            logkw.write("Duration: {:.2f}s\n".format(duration))
            logkw.write("\n" + "="*40 + "\n")
            
        is_correct, status, _ = verify_json(response_content, puzzle.ground_truth)
        with open(log_filename, "a") as logkw:
            logkw.write(f"Correct: {is_correct}\n")
            logkw.write(f"Status: {status}\n")

        print(f"Result for {model}: {status} ({duration:.2f}s)")
        print(f"Logged details to {log_filename}")


            
    except Exception as e:
        print(f"Error evaluating {model}: {e}")
        traceback.print_exc()
        
        # Log exception to file
        with open(log_filename, "w") as logkw:
            logkw.write(f"Model: {model}\n")
            logkw.write(f"Puzzle ID: {puzzle_counter}\n")
            logkw.write("STATUS: EVALUATION_ERROR\n")
            logkw.write(f"Error: {str(e)}\n")
            logkw.write("\nTRACEBACK:\n")
            logkw.write(traceback.format_exc())

def generate_execution_configs(args):
    """
    Generates a list of execution tasks (tuples) by pre-generating puzzles.
    Handles puzzle generation and logging of generation errors immediately.
    Returns: list of (model, puzzle, puzzle_counter, n, m, dry_run)
    """
    configs = []
    puzzle_counter = 0
    
    for n in range(args.n_min, args.n_max + 1):
        for m in range(args.m_min, args.m_max + 1):
            for r in range(args.repeats):
                puzzle_counter += 1
                print(f"\n--- Generating Puzzle #{puzzle_counter} (N={n}, M={m}) ---")
                
                # Loop MODELS FIRST so we can try to generate a puzzle for each model independently
                for model in args.models:
                    try:
                        puzzle = LogicPuzzle(n, m)
                        puzzle.generate_ground_truth()
                        # Clues generated later in thread
                        
                        configs.append((model, puzzle, puzzle_counter, n, m, args.dry_run))
                        
                    except Exception as e:
                        # Log initialization error immediately for this model
                        print(f"Error initializing puzzle #{puzzle_counter} for {model}: {e}")
                        traceback.print_exc()
                        
                        log_filename = get_log_filename(puzzle_counter, n, m, model)
                        with open(log_filename, "w") as logkw:
                            logkw.write(f"Model: {model}\n")
                            logkw.write(f"Puzzle ID: {puzzle_counter}\n")
                            logkw.write("STATUS: GENERATION_ERROR\n")
                            logkw.write(f"Error: {str(e)}\n")
                            logkw.write("\nTRACEBACK:\n")
                            logkw.write(traceback.format_exc())
                        

                            
    random.shuffle(configs)                        
    return configs

def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Run Logic Puzzle Evaluation")
    parser.add_argument("--models", nargs="+", default=["openai/gpt-3.5-turbo"], help="List of models to evaluate")
    parser.add_argument("--n-min", type=int, default=2, help="Min number of people")
    parser.add_argument("--n-max", type=int, default=4, help="Max number of people")
    parser.add_argument("--m-min", type=int, default=2, help="Min number of attributes")
    parser.add_argument("--m-max", type=int, default=4, help="Max number of attributes")
    parser.add_argument("--repeats", type=int, default=1, help="Number of puzzles per configuration")
    
    parser.add_argument("--dry-run", action="store_true", help="Generate puzzles without querying the LLM")
    
    args = parser.parse_args()
    
    print(f"Starting evaluation across {len(args.models)} models...")
    print(f"Grid: People {args.n_min}-{args.n_max}, Attributes {args.m_min}-{args.m_max}")

    # Phase 1: Generate all puzzles and tasks
    execution_configs = generate_execution_configs(args)
    print(f"\nGenerated {len(execution_configs)} execution tasks.")
    
    # Phase 2: Execute tasks in parallel
    # We use ThreadPoolExecutor to run models across ALL puzzles in parallel.
    # We set max_workers to 300 to allow massive concurrency.
    all_futures = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=300) as executor:
        for config in execution_configs:
            # config is (model, puzzle, puzzle_counter, n, m, dry_run)
            all_futures.append(executor.submit(evaluate_model, *config))
        
        # Wait for ALL puzzles to complete
        if all_futures:
            print(f"\nSubmissions complete. Waiting for {len(all_futures)} evaluations...")
            concurrent.futures.wait(all_futures)
        else:
            print("\nNo tasks to execute (generation errors or empty config).")

if __name__ == "__main__":
    main()
