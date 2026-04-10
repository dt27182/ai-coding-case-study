import argparse
import os
import traceback
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from generate_puzzle import generate_puzzle
from solve_puzzle import create_solver_with_clues
from llm_interface import OpenRouterClient, extract_solution_json
from evaluator import evaluate_solution, calculate_accuracy
from logger import ResultLogger


class RateLimiter:
    """Simple rate limiter that enforces a maximum number of requests per minute."""
    
    def __init__(self, max_requests_per_minute):
        self.max_requests_per_minute = max_requests_per_minute
        self.request_times = []
        self.lock = threading.Lock()
    
    def acquire(self):
        """Block until a request can be made within the rate limit."""
        with self.lock:
            current_time = time.time()
            
            # Remove requests older than 1 minute
            self.request_times = [t for t in self.request_times if current_time - t < 60]
            
            # If we're at the limit, wait until the oldest request expires
            if len(self.request_times) >= self.max_requests_per_minute:
                oldest_request = self.request_times[0]
                wait_time = 60 - (current_time - oldest_request)
                if wait_time > 0:
                    time.sleep(wait_time)
                    current_time = time.time()
                    # Clean up again after waiting
                    self.request_times = [t for t in self.request_times if current_time - t < 60]
            
            # Record this request
            self.request_times.append(current_time)


def main():
    parser = argparse.ArgumentParser(description="Zebra Puzzle LLM Evaluation System")
    parser.add_argument('-m', '--models', nargs='+', default=['tngtech/deepseek-r1t2-chimera:free'], help='List of model names to test')
    parser.add_argument('-n', '--num-puzzles', type=int, default=1, help='Number of puzzles to generate')
    parser.add_argument('-p', '--min-people', type=int, default=3, help='Minimum number of people in puzzles')
    parser.add_argument('-P', '--max-people', type=int, default=4, help='Maximum number of people in puzzles')
    parser.add_argument('-a', '--min-attributes', type=int, default=3, help='Minimum number of attributes per person')
    parser.add_argument('-A', '--max-attributes', type=int, default=3, help='Maximum number of attributes per person')
    parser.add_argument('-r', '--results-dir', default='results', help='Directory to save results')
    parser.add_argument('--rate-limit', type=int, default=20, help='Maximum LLM requests per minute (default: 20)')
    
    args = parser.parse_args()
    
    api_key = os.environ.get('OPEN_ROUTER_TOKEN')
    
    client = OpenRouterClient(api_key)
    logger = ResultLogger(args.results_dir)
    rate_limiter = RateLimiter(args.rate_limit)
    
    model_results = {model: [] for model in args.models}
    
    configurations = [
        (num_people, num_attributes)
        for num_people in range(args.min_people, args.max_people + 1)
        for num_attributes in range(args.min_attributes, args.max_attributes + 1)
    ]
    
    total_puzzles = len(configurations) * args.num_puzzles
    
    print(f"Testing {len(configurations)} configurations x {args.num_puzzles} puzzles = {total_puzzles} total puzzles")
    print(f"People range: {args.min_people}-{args.max_people}")
    print(f"Attributes range: {args.min_attributes}-{args.max_attributes}")
    print(f"Configurations: {configurations}")
    print(f"Models: {', '.join(args.models)}")
    print(f"Rate limit: {args.rate_limit} requests per minute")
    print()
    
    print("Generating puzzles...")
    puzzles = []
    puzzle_id = 0
    for num_people, num_attributes in configurations:
        for iteration in range(args.num_puzzles):
            print(f"  [{puzzle_id + 1}/{total_puzzles}] Generating {num_people}x{num_attributes} puzzle {iteration + 1}/{args.num_puzzles}...")
            
            puzzle = generate_puzzle(num_people, num_attributes)
            
            solver = create_solver_with_clues(
                puzzle['num_people'],
                puzzle['attributes'],
                puzzle['clues']
            )
            ground_truth = solver.solve()
            
            puzzles.append({
                'puzzle_id': puzzle_id,
                'num_people': num_people,
                'num_attributes': num_attributes,
                'puzzle': puzzle,
                'ground_truth': ground_truth
            })
            puzzle_id += 1
    
    print(f"\nQuerying models in parallel...")
    
    def query_task(puzzle_data, model_name):
        puzzle_id = puzzle_data['puzzle_id']
        puzzle = puzzle_data['puzzle']
        ground_truth = puzzle_data['ground_truth']
        
        try:
            prompt = client.create_prompt(puzzle['text'])
            logger.log_initial(model_name, puzzle_id, puzzle_data, prompt)
            
            # Apply rate limiting before making the LLM request
            rate_limiter.acquire()
            
            llm_result = client.query_model(model_name, puzzle['text'])
            
            extracted_solution = extract_solution_json(llm_result['response'])
            
            evaluation = evaluate_solution(extracted_solution, ground_truth)
            
            result_data = {
                'puzzle_id': puzzle_id,
                'configuration': f"{puzzle_data['num_people']}x{puzzle_data['num_attributes']}",
                'num_people': puzzle_data['num_people'],
                'num_attributes': puzzle_data['num_attributes'],
                'ground_truth': ground_truth,
                'prompt': llm_result['prompt'],
                'response': llm_result['response'],
                'full_response': llm_result.get('full_response'),
                'extracted_solution': extracted_solution,
                'evaluation': evaluation,
                'elapsed_time': llm_result['elapsed_time'],
                'error': llm_result['error'],
                'timestamp': llm_result['timestamp'],
                'errored': False
            }
            
            logger.log_result(model_name, puzzle_id, result_data)
            
            status = "✓" if evaluation['correct'] else "✗"
            config = f"{puzzle_data['num_people']}x{puzzle_data['num_attributes']}"
            print(f"  {status} [{config} #{puzzle_id}] {model_name}: {evaluation['reason']}")
            
            return model_name, result_data
        except Exception as e:
            error_msg = str(e)
            error_traceback = traceback.format_exc()
            config = f"{puzzle_data['num_people']}x{puzzle_data['num_attributes']}"
            print(f"  ✗ [{config} #{puzzle_id}] {model_name}: Exception - {error_msg}")
            
            logger.log_exception(model_name, puzzle_id, puzzle_data, error_msg, error_traceback)
            
            result_data = {
                'puzzle_id': puzzle_id,
                'configuration': f"{puzzle_data['num_people']}x{puzzle_data['num_attributes']}",
                'num_people': puzzle_data['num_people'],
                'num_attributes': puzzle_data['num_attributes'],
                'ground_truth': ground_truth,
                'evaluation': {'correct': False, 'reason': f'Exception: {error_msg}'},
                'error': error_msg,
                'errored': True
            }
            
            return model_name, result_data
    
    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(query_task, puzzle_data, model_name)
            for puzzle_data in puzzles
            for model_name in args.models
        ]
        
        for future in as_completed(futures):
            try:
                model_name, result_data = future.result()
                model_results[model_name].append(result_data)
            except Exception as e:
                print(f"Error processing task: {e}")
    
    print()
    
    print("=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)
    
    model_accuracy = {}
    for model_name, results in model_results.items():
        accuracy = calculate_accuracy(results)
        model_accuracy[model_name] = accuracy
        print(f"{model_name}: {accuracy:.2%} ({sum(1 for r in results if r['evaluation']['correct'])}/{len(results)})")
    
    summary_data = {
        'total_puzzles': total_puzzles,
        'configurations': configurations,
        'puzzles_per_config': args.num_puzzles,
        'models': args.models,
        'model_accuracy': model_accuracy
    }
    logger.log_summary(summary_data)
    
    print()
    print(f"Results saved to {args.results_dir}/")


if __name__ == '__main__':
    main()
