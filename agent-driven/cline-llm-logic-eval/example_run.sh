#!/bin/bash

# Example script to run a small evaluation
# Make sure OPEN_ROUTER_TOKEN environment variable is set before running

echo "================================"
echo "Logic Puzzle LLM Evaluation"
echo "Example Run Script"
echo "================================"
echo ""

# Check if API key is set
if [ -z "$OPEN_ROUTER_TOKEN" ]; then
    echo "ERROR: OPEN_ROUTER_TOKEN environment variable is not set"
    echo "Please set it with: export OPEN_ROUTER_TOKEN='your-api-key'"
    exit 1
fi

echo "Running small test evaluation..."
echo "  - Testing 2 people with 2 categories"
echo "  - Using anthropic/claude-3-haiku model"
echo ""

python3 run_evaluation.py \
  --min-people 2 \
  --max-people 2 \
  --min-categories 2 \
  --max-categories 2 \
  --models anthropic/claude-3-haiku \
  --output-dir logs

echo ""
echo "================================"
echo "Evaluation complete!"
echo "Now analyzing results..."
echo "================================"
echo ""

python3 analyze_results.py --log-dir logs --output analysis_results.csv

echo ""
echo "================================"
echo "Done! Check analysis_results.csv"
echo "================================"
