import json
import os
import re
import sys
import time
import threading
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.chdir(os.path.join(os.path.dirname(__file__), '..'))

from clues import AdjacencyClue, AttributeRelationClue, DirectClue
from execute_tests import (
    compare_solutions,
    puzzle_to_text,
    run_sample,
)


# ---------------------------------------------------------------------------
# Property 5: Successful live OpenRouter API call
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not os.environ.get('OPEN_ROUTER_TOKEN'),
    reason="OPEN_ROUTER_TOKEN not set"
)
def test_live_openrouter_api_call():
    from openai import OpenAI

    client = OpenAI(
        api_key=os.environ['OPEN_ROUTER_TOKEN'],
        base_url="https://openrouter.ai/api/v1",
    )
    import re, tempfile
    with tempfile.NamedTemporaryFile(mode='r', suffix='.txt', delete=False) as f:
        log_path = f.name
    run_sample("openai/gpt-4o-mini", client, log_path, 2, 2, 1, 1, dry_run=False)
    with open(log_path) as f:
        content = f.read()

    assert ">>> ERROR" not in content, f"run_sample raised an error:\n{content}"
    assert ">>> RAW API RESPONSE" in content, "No API response was logged"
    assert ">>> LLM OUTPUT TEXT" in content
    assert ">>> SOLUTION COMPARISON" in content

    match = re.search(r'>>> RAW API RESPONSE\n\n(.*?)\n>>> ', content, re.DOTALL)
    assert match, "Could not extract RAW API RESPONSE block"
    raw = json.loads(match.group(1).strip())
    assert raw.get("error") is None, f"Expected error=null in response, got: {raw.get('error')}"


# ---------------------------------------------------------------------------
# Property 6: Text representation matches expected format
# ---------------------------------------------------------------------------

FIXED_PUZZLE = {
    'solution': [
        {"Position": 0, "Name": "Alice", "Job": "Doctor"},
        {"Position": 1, "Name": "Bob",   "Job": "Farmer"},
    ],
    'clues': [
        DirectClue(position=0, attribute="Name", value="Alice"),
        AttributeRelationClue(attr1="Name", val1="Alice", attr2="Job", val2="Doctor"),
        AdjacencyClue(attribute="Name", left_val="Alice", right_val="Bob"),
    ],
}


def test_puzzle_to_text_opening_description():
    text = puzzle_to_text(FIXED_PUZZLE)
    assert text.startswith("There are 2 people attending a party.")


def test_puzzle_to_text_possible_values():
    text = puzzle_to_text(FIXED_PUZZLE)
    assert "The possible values for Name are:" in text
    assert "The possible values for Job are:" in text


def test_puzzle_to_text_clues_section_header():
    text = puzzle_to_text(FIXED_PUZZLE)
    assert "Below are a set of clues about each person." in text


def test_puzzle_to_text_direct_clue_format():
    text = puzzle_to_text(FIXED_PUZZLE)
    assert "The person sitting at position 0 has Alice as their Name." in text


def test_puzzle_to_text_attribute_relation_clue_format():
    text = puzzle_to_text(FIXED_PUZZLE)
    assert "The person who has Alice as their Name also has Doctor as their Job." in text


def test_puzzle_to_text_adjacency_clue_format():
    text = puzzle_to_text(FIXED_PUZZLE)
    assert "is sitting to the left of" in text


def test_puzzle_to_text_solution_instructions():
    text = puzzle_to_text(FIXED_PUZZLE)
    assert (
        "Please write the answer as a JSON array demarked within <solution></solution> tags, "
        "where each element is a JSON object. Do not include anything else in the output. For example:"
    ) in text


def test_puzzle_to_text_solution_tags():
    import re
    text = puzzle_to_text(FIXED_PUZZLE)
    # Find all <solution>...</solution> blocks; the last one contains the JSON example
    matches = re.findall(r'<solution>(.*?)</solution>', text, re.DOTALL)
    assert matches, "No <solution> block found"
    # The example block has non-empty content (JSON array)
    example_blocks = [m.strip() for m in matches if m.strip()]
    assert example_blocks, "No non-empty <solution> block found"
    example = json.loads(example_blocks[-1])
    assert isinstance(example, list)
    assert len(example) == 2
    assert all("Position" in item for item in example)


# ---------------------------------------------------------------------------
# Property 7: Solution comparison logic is deterministic and logically correct
# ---------------------------------------------------------------------------

EXPECTED = [
    {"Position": 0, "Name": "Alice", "Job": "Doctor"},
    {"Position": 1, "Name": "Bob",   "Job": "Farmer"},
]


def test_compare_solutions_exact_match():
    llm = [
        {"Position": 0, "Name": "Alice", "Job": "Doctor"},
        {"Position": 1, "Name": "Bob",   "Job": "Farmer"},
    ]
    assert compare_solutions(EXPECTED, llm) == []


def test_compare_solutions_one_wrong_value():
    llm = [
        {"Position": 0, "Name": "WRONG", "Job": "Doctor"},
        {"Position": 1, "Name": "Bob",   "Job": "Farmer"},
    ]
    mismatches = compare_solutions(EXPECTED, llm)
    assert any("Position 0" in m and "Name" in m for m in mismatches)
    assert len(mismatches) == 1


def test_compare_solutions_unknown_position():
    llm = [
        {"Position": 99, "Name": "Alice", "Job": "Doctor"},
    ]
    mismatches = compare_solutions(EXPECTED, llm)
    assert any("Position 99" in m for m in mismatches)


def test_compare_solutions_order_independent():
    llm = [
        {"Position": 1, "Name": "Bob",   "Job": "Farmer"},
        {"Position": 0, "Name": "Alice", "Job": "Doctor"},
    ]
    assert compare_solutions(EXPECTED, llm) == []


# ---------------------------------------------------------------------------
# Property 8: Parallel execution with up to 1000 concurrent calls
# ---------------------------------------------------------------------------

def test_parallel_execution():
    SLEEP_DURATION = 0.2
    NUM_INVOCATIONS = 16  # 4 people configs x 4 attr configs
    lock = threading.Lock()
    start_times = []

    def mock_generate_puzzle(num_people, num_attrs):
        with lock:
            start_times.append(time.time())
        time.sleep(SLEEP_DURATION)
        solution = [{"Position": i, "Name": f"Person{i}"} for i in range(num_people)]
        return {"solution": solution, "clues": []}

    with patch('sys.argv', [
        'execute_tests',
        '-p', '2', '-P', '5',
        '-a', '2', '-A', '5',
        '-n', '1', '-m', 'test-model', '--dry-run',
    ]):
        with patch.dict(os.environ, {'OPEN_ROUTER_TOKEN': 'fake_token'}):
            with patch('execute_tests.generate_puzzle', side_effect=mock_generate_puzzle):
                with patch('execute_tests.OpenAI', return_value=MagicMock()):
                    import execute_tests
                    wall_start = time.time()
                    execute_tests.main()
                    wall_elapsed = time.time() - wall_start

    sequential_time = NUM_INVOCATIONS * SLEEP_DURATION
    assert wall_elapsed < sequential_time, (
        f"Wall time {wall_elapsed:.2f}s >= sequential time {sequential_time:.2f}s — not parallel"
    )


# ---------------------------------------------------------------------------
# Property 8b: All puzzle configs in range are run
# ---------------------------------------------------------------------------

def _run_main_collect_log_files(argv, tmp_path):
    """Run main() in tmp_path and return parsed (num_people, num_attrs, sample) from log filenames."""
    import execute_tests
    orig = os.getcwd()
    try:
        os.chdir(tmp_path)
        with patch('sys.argv', argv):
            with patch.dict(os.environ, {'OPEN_ROUTER_TOKEN': 'fake_token'}):
                with patch('execute_tests.generate_puzzle', side_effect=lambda p, _a: {
                    "solution": [{"Position": i, "Name": f"P{i}"} for i in range(p)], "clues": [],
                }):
                    with patch('execute_tests.OpenAI', return_value=MagicMock()):
                        execute_tests.main()
    finally:
        os.chdir(orig)

    configs = []
    for path in tmp_path.glob("logs/**/*.txt"):
        m = re.match(r'p(\d+)_a(\d+)_s(\d+)_', path.name)
        if m:
            configs.append((int(m.group(1)), int(m.group(2)), int(m.group(3))))
    return configs


def test_all_configs_run_full_range(tmp_path):
    configs = _run_main_collect_log_files([
        'execute_tests', '-p', '2', '-P', '4', '-a', '3', '-A', '5', '-n', '1', '-m', 'model-a', '--dry-run',
    ], tmp_path)
    expected = {(p, a, 1) for p in range(2, 5) for a in range(3, 6)}
    assert set(configs) == expected


def test_all_configs_run_single_people_value(tmp_path):
    configs = _run_main_collect_log_files([
        'execute_tests', '-p', '3', '-P', '3', '-a', '2', '-A', '4', '-n', '1', '-m', 'model-a', '--dry-run',
    ], tmp_path)
    expected = {(3, a, 1) for a in range(2, 5)}
    assert set(configs) == expected


def test_all_configs_run_single_attrs_value(tmp_path):
    configs = _run_main_collect_log_files([
        'execute_tests', '-p', '2', '-P', '5', '-a', '4', '-A', '4', '-n', '1', '-m', 'model-a', '--dry-run',
    ], tmp_path)
    expected = {(p, 4, 1) for p in range(2, 6)}
    assert set(configs) == expected


def test_all_configs_run_multiple_samples(tmp_path):
    configs = _run_main_collect_log_files([
        'execute_tests', '-p', '2', '-P', '3', '-a', '2', '-A', '3', '-n', '3', '-m', 'model-a', '--dry-run',
    ], tmp_path)
    # 4 configs × 3 samples = 12 log files
    expected = {(p, a, s) for p in range(2, 4) for a in range(2, 4) for s in range(1, 4)}
    assert set(configs) == expected


def test_all_configs_run_multiple_models(tmp_path):
    configs = _run_main_collect_log_files([
        'execute_tests', '-p', '2', '-P', '3', '-a', '2', '-A', '3', '-n', '1', '-m', 'model-a', 'model-b', '--dry-run',
    ], tmp_path)
    # Each model gets its own log directory; 4 configs × 2 models = 8 log files
    assert len(configs) == 8
    expected_configs = {(p, a, 1) for p in range(2, 4) for a in range(2, 4)}
    assert {(p, a, s) for p, a, s in configs} == expected_configs


# ---------------------------------------------------------------------------
# Property 9: Log files in correct directory and format (integration test)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not os.environ.get('OPEN_ROUTER_TOKEN'),
    reason="OPEN_ROUTER_TOKEN not set"
)
def test_log_format_and_api_response(tmp_path):
    from openai import OpenAI

    client = OpenAI(
        api_key=os.environ['OPEN_ROUTER_TOKEN'],
        base_url="https://openrouter.ai/api/v1",
    )
    log_path = str(tmp_path / "p2_a2_s1_test.txt")

    run_sample("openai/gpt-4o-mini", client, log_path, 2, 2, 1, 1, dry_run=False)

    assert os.path.exists(log_path), "Log file was not created"
    with open(log_path) as f:
        content = f.read()

    for section in ["# SAMPLE 1/1", ">>> PUZZLE PROMPT", ">>> RAW API RESPONSE",
                    ">>> LLM OUTPUT TEXT", ">>> SOLUTION COMPARISON"]:
        assert section in content, f"Missing section: {section}"

    # Extract and parse the RAW API RESPONSE JSON
    import re
    match = re.search(r'>>> RAW API RESPONSE\n\n(.*?)\n>>> ', content, re.DOTALL)
    assert match, "Could not extract RAW API RESPONSE block"
    raw_json = match.group(1).strip()
    parsed = json.loads(raw_json)

    # Verify key fields from the actual OpenRouter response are present
    for field in ("id", "model", "output", "object"):
        assert field in parsed, f"Expected field '{field}' in logged API response"


# ---------------------------------------------------------------------------
# Property 10: All exceptions caught and logged
# ---------------------------------------------------------------------------

def test_exception_in_puzzle_generation_is_caught_and_logged(tmp_path):
    client = MagicMock()
    log_path = str(tmp_path / "log.txt")
    with patch('execute_tests.generate_puzzle', side_effect=RuntimeError("gen error")):
        run_sample("test-model", client, log_path, 2, 2, 1, 1, dry_run=False)
    content = open(log_path).read()
    assert ">>> ERROR" in content
    assert "RuntimeError" in content
    assert "gen error" in content


def test_exception_in_api_call_is_caught_and_logged(tmp_path):
    client = MagicMock()
    client.responses.create.side_effect = ConnectionError("API down")
    log_path = str(tmp_path / "log.txt")
    with patch('execute_tests.generate_puzzle', return_value={
        'solution': [{"Position": 0, "Name": "Alice"}, {"Position": 1, "Name": "Bob"}],
        'clues': [],
    }):
        run_sample("test-model", client, log_path, 2, 2, 1, 1, dry_run=False)
    content = open(log_path).read()
    assert ">>> ERROR" in content
    assert "ConnectionError" in content
    assert "API down" in content


def test_exception_in_compare_solutions_is_caught_and_logged(tmp_path):
    client = MagicMock()
    fake_solution = [{"Position": 0, "Name": "Alice"}, {"Position": 1, "Name": "Bob"}]
    fake_response = MagicMock()
    fake_response.output_text = '<solution>[{"Position": 0, "Name": "Alice"}, {"Position": 1, "Name": "Bob"}]</solution>'
    fake_response.model_dump.return_value = {"id": "r1", "model": "test", "output": []}
    client.responses.create.return_value = fake_response

    log_path = str(tmp_path / "log.txt")
    with patch('execute_tests.generate_puzzle', return_value={
        'solution': fake_solution,
        'clues': [],
    }):
        with patch('execute_tests.compare_solutions', side_effect=ValueError("compare error")):
            run_sample("test-model", client, log_path, 2, 2, 1, 1, dry_run=False)
    content = open(log_path).read()
    assert ">>> ERROR" in content
    assert "ValueError" in content
    assert "compare error" in content
