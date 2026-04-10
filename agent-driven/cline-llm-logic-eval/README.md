# Logic Puzzle LLM Evaluation

A Python program for generating logic grid puzzles (Einstein-style), testing LLMs via OpenRouter API, and comparing their solutions to ground truth.

## Features

- **Configurable Puzzle Generation**: Generate logic grid puzzles with 1-20 people and 1-20 attribute categories
- **Multi-Model Testing**: Test multiple LLM models simultaneously via OpenRouter API
- **Comprehensive Logging**: All puzzle prompts, solutions, API responses, and comparisons are logged
- **Detailed Analytics**: Generate 2D grid reports showing accuracy metrics by puzzle complexity

## Requirements

- Python 3.7+
- OpenRouter API key (set as `OPEN_ROUTER_TOKEN` environment variable)

## Installation

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set your OpenRouter API key:
```bash
export OPEN_ROUTER_TOKEN="your-api-key-here"
```

## Usage

### Running Evaluations

Use `run_evaluation.py` to generate puzzles and test LLMs:

```bash
python run_evaluation.py \
  --min-people 2 \
  --max-people 4 \
  --min-categories 2 \
  --max-categories 3 \
  --models anthropic/claude-3-haiku openai/gpt-4 \
  --output-dir logs
```

**Arguments:**
- `--min-people`: Minimum number of people in puzzles (1-20)
- `--max-people`: Maximum number of people in puzzles (1-20)
- `--min-categories`: Minimum number of attribute categories (1-20)
- `--max-categories`: Maximum number of attribute categories (1-20)
- `--models`: Space-separated list of model identifiers (OpenRouter format)
- `--output-dir`: Directory to save log files (default: `logs`)
- `--seed`: Optional random seed for reproducibility

**Example:**
```bash
# Test 2-3 people with 2-3 categories using Claude Haiku
python run_evaluation.py \
  --min-people 2 \
  --max-people 3 \
  --min-categories 2 \
  --max-categories 3 \
  --models anthropic/claude-3-haiku \
  --output-dir my_logs
```

This will generate puzzles for all combinations:
- 2 people, 2 categories
- 2 people, 3 categories
- 3 people, 2 categories
- 3 people, 3 categories

Each combination will be tested with each specified model, and results will be saved to individual JSON log files.

### Analyzing Results

Use `analyze_results.py` to generate CSV reports from log files:

```bash
python analyze_results.py --log-dir logs --output analysis_results.csv
```

**Arguments:**
- `--log-dir`: Directory containing log files (required)
- `--output`: Output CSV filename (default: `analysis_results.csv`)
- `--model`: Filter by specific model (optional)

**Output:**

The analysis script generates CSV files containing four 2D grids:

1. **Correct Count Grid**: Number of correct solutions (rows = people, columns = categories)
2. **Total Count Grid**: Total number of test runs
3. **Pass Rate Grid**: Success rate (correct/total) as decimal
4. **Error Count Grid**: Number of runs that errored out

When run without `--model` filter, it generates:
- One combined report for all models
- Individual reports for each model found in the logs

### Puzzle Format

Generated puzzles follow this format:

```
There are N people attending a party. Everyone is sitting in a row. 
The left most seat will be referred to as position 0, the next seat 
to the right will be referred to as position 1 and so on. 
Each person has a [list of categories].

The possible values for [category1] are: [values]
The possible values for [category2] are: [values]
...

Below are a set of clues about each person.

[Clue 1]. [Clue 2]. [Clue 3]...

Can you figure out what each person's [categories] are?

Please write the anwser as a JSON array demarked with in <solution></solution> tags...
```

### Log File Structure

Each evaluation creates a JSON log file with:

```json
{
  "timestamp": "2024-01-01T12:00:00",
  "num_people": 3,
  "num_categories": 3,
  "model": "anthropic/claude-3-haiku",
  "puzzle_prompt": "...",
  "expected_solution": [...],
  "llm_response": {
    "success": true,
    "response": {...},
    "raw_response_text": "...",
    "parsed_solution": [...],
    "elapsed_time": 2.5
  },
  "parsed_llm_solution": [...],
  "comparison": {
    "correct": true,
    "details": "Solution matches exactly"
  },
  "correct": true,
  "status": "completed"
}
```

If an error occurs during generation, API call, or parsing, it will be logged in the `error` and `traceback` fields.

## Project Structure

```
.
├── puzzle_generator.py    # Logic puzzle generation module
├── llm_tester.py          # OpenRouter API integration and solution comparison
├── run_evaluation.py      # Main evaluation runner script
├── analyze_results.py     # Results analysis and CSV generation
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## OpenRouter Models

You can use any model available on OpenRouter. Some examples:

- `anthropic/claude-3-opus`
- `anthropic/claude-3-sonnet`
- `anthropic/claude-3-haiku`
- `openai/gpt-4-turbo`
- `openai/gpt-4`
- `openai/gpt-3.5-turbo`
- `google/gemini-pro`
- `meta-llama/llama-2-70b-chat`

Check [OpenRouter's documentation](https://openrouter.ai/docs) for the full list of available models.

## Example Workflow

1. **Run a small test evaluation:**
```bash
python run_evaluation.py \
  --min-people 2 \
  --max-people 2 \
  --min-categories 2 \
  --max-categories 2 \
  --models anthropic/claude-3-haiku
```

2. **Check the logs:**
```bash
ls -lh logs/
cat logs/p2_c2_*.json | head -50
```

3. **Analyze results:**
```bash
python analyze_results.py --log-dir logs
```

4. **View the CSV:**
```bash
open analysis_results.csv  # macOS
# or
cat analysis_results.csv
```

## Testing Individual Components

Each module can be tested individually:

```bash
# Test puzzle generator
python puzzle_generator.py

# Test LLM tester (requires OPEN_ROUTER_TOKEN)
python llm_tester.py
```

## Notes

- The puzzle generator uses a comprehensive set of predefined categories (names, colors, pets, drinks, countries, etc.)
- **Puzzles are verified to have a unique solution** using a CSP (Constraint Satisfaction Problem) solver
- The generator creates three types of clues:
  - **Relationship clues**: "The person who has X as their A also has Y as their B"
  - **Direct position clues**: "The person sitting at position N has X as their A"
  - **Relative position clues**: "The person who has X as their A is sitting to the left of the person who has Y as their B"
- The comparison is exact match only - all attributes for all people must match
- API calls timeout after 120 seconds by default
- Each puzzle-model combination gets a unique log file with timestamp

## Troubleshooting

**"OpenRouter API key not provided"**
- Make sure to set the `OPEN_ROUTER_TOKEN` environment variable

**"No valid log files found"**
- Check that the log directory path is correct
- Ensure evaluations have been run and logs were created

**Pylance type warnings**
- These are static analysis warnings and don't affect functionality
- The code handles None values appropriately at runtime

## License

This project is provided as-is for evaluation purposes.
