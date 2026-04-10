# Zebra Puzzle LLM Evaluation System

A Python system that generates procedurally-created Zebra logic puzzles, queries multiple LLMs via OpenRouter, and evaluates their solution accuracy.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py \
  --models "anthropic/claude-3-sonnet" "openai/gpt-4" \
  --api-key YOUR_OPENROUTER_API_KEY \
  --num-puzzles 10 \
  --min-people 3 \
  --max-people 5 \
  --min-attributes 3 \
  --max-attributes 5
```

## Arguments

- `--models`: List of model names to test (space-separated)
- `--api-key`: Your OpenRouter API key
- `--num-puzzles`: Number of puzzles to generate (default: 10)
- `--min-people`: Minimum number of people in puzzles (default: 3)
- `--max-people`: Maximum number of people in puzzles (default: 5)
- `--min-attributes`: Minimum number of attributes per person (default: 3)
- `--max-attributes`: Maximum number of attributes per person (default: 5)
- `--results-dir`: Directory to save results (default: results)

## Output

Results are saved to the `results/` directory:
- `results/{model_name}/puzzle_{id}.txt`: Detailed logs for each puzzle and model
- `results/summary.txt`: Overall accuracy summary

## Example

```bash
python main.py \
  --models "anthropic/claude-3-sonnet" "openai/gpt-4-turbo" \
  --api-key sk-or-v1-xxx \
  --num-puzzles 5 \
  --min-people 3 \
  --max-people 4 \
  --min-attributes 3 \
  --max-attributes 4
```

## How It Works

1. **Puzzle Generation**: Procedurally generates Zebra puzzles with varying difficulty
2. **Constraint Solving**: Uses python-constraint library to ensure puzzles have unique solutions
3. **LLM Querying**: Sends puzzles to multiple models in parallel via OpenRouter
4. **Solution Extraction**: Extracts JSON solutions from LLM responses
5. **Evaluation**: Compares LLM solutions against ground truth for exact match
6. **Logging**: Saves all run details for later analysis
