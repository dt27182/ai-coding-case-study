## Plan: Zebra Puzzle LLM Evaluation System

Build a Python program that procedurally generates solvable Zebra puzzles with iterative clue validation, queries multiple LLMs via OpenRouter with parallel requests, extracts JSON answers, and evaluates accuracy against ground-truth solutions. All LLM interactions and failures are logged as plain text for analysis.

### Steps
1. Create a Zebra puzzle generator (`puzzle_generator.py`) that creates constraint definitions, iteratively adds randomized clues, validates solvability via CSP solver, and outputs puzzles as human-readable text with difficulty randomized by person/attribute counts within user-specified ranges.
2. Build a CSP-based puzzle solver (`puzzle_solver.py`) using the `python-constraint` library that validates puzzle solvability, generates ground-truth solutions in JSON format `{"person_id": {"attribute_name": "value"}, ...}`, and provides constraint checking utilities.
3. Implement the OpenRouter LLM interface (`llm_interface.py`) that formats puzzle prompts with strict JSON output instructions wrapped in `<solution></solution>` tags, sends parallel requests to multiple models using `concurrent.futures.ThreadPoolExecutor`, captures full request/response metadata, and extracts JSON from within the solution tags.
4. Create an evaluation module (`evaluator.py`) that parses LLM JSON responses and compares against ground-truth for exact-match accuracy, handling parse errors gracefully.
5. Build a logging system (`logger.py`) that saves all LLM run details (input prompt, model name, raw output, extracted JSON, errors, timing) as plain text files in `results/{model_name}/puzzle_{id}.txt` structure.
6. Implement a CLI entry point (`main.py`) that accepts model names, puzzle parameters (count, person range, attribute range), orchestrates the full pipeline with parallel LLM calls, and outputs accuracy metrics.

### Further Considerations
1. **JSON extraction robustness:** Extract multi-line JSON content from within `<solution></solution>` tags. Simple regex pattern: `<solution>(.*?)</solution>` with DOTALL flag.
2. **Parallel request strategy:** Use `concurrent.futures.ThreadPoolExecutor` for simpler implementation with standard requests library.
3. **Logging output structure:** Create directory per model (`results/{model_name}/`) and save separate files per puzzle run (`puzzle_{id}.txt`).
4. Do not use python virtual environments; just use the global python3 environment.