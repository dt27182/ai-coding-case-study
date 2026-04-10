# Implementation Guide

The test suite in `tests/` validates two modules: `generate_puzzle.py` and `execute_tests.py`. A third module `clues.py` defines shared data types used by both.

---

## `clues.py`

Define three dataclasses (or namedtuples):

```python
DirectClue(position, attribute, value)
AttributeRelationClue(attr1, val1, attr2, val2)
AdjacencyClue(attribute, left_val, right_val)
```

Also export three generator functions used in tests:
```python
gen_direct_clues(solution) -> list[DirectClue]
gen_attribute_relation_clues(solution) -> list[AttributeRelationClue]
gen_adjacency_clues(solution) -> list[AdjacencyClue]
```

`solution` is a list of dicts like `[{"Position": 0, "Name": "Alice", "Job": "Doctor"}, ...]`.

---

## `generate_puzzle.py`

Export one function:
```python
generate_puzzle(num_people: int, num_attributes: int) -> dict
```

Returns `{"solution": [...], "clues": [...], "num_clues": int}`.

- `solution` is a list of `num_people` dicts, each with `"Position"` (0-indexed int) plus one key per attribute
- `clues` is a list of `DirectClue`, `AttributeRelationClue`, and `AdjacencyClue` objects that together uniquely determine the solution (verified by CSP)
- Must complete within **15 seconds** for configs up to 20×20

---

## `execute_tests.py`

Export three functions and a `main()`:

```python
puzzle_to_text(puzzle: dict) -> str
```
Converts a puzzle dict to a prompt string. Must contain:
- Opening: `"There are N people attending a party."`
- `"The possible values for {attr} are: ..."` for each attribute
- `"Below are a set of clues about each person."`
- Clue sentences in specific formats (see below)
- Instructions ending with: `"Please write the answer as a JSON array demarked within <solution></solution> tags, where each element is a JSON object. Do not include anything else in the output. For example:"`
- A `<solution>[...]</solution>` block with a JSON example array

Clue sentence formats:
- `DirectClue` → `"The person sitting at position {pos} has {val} as their {attr}."`
- `AttributeRelationClue` → `"The person who has {val1} as their {attr1} also has {val2} as their {attr2}."`
- `AdjacencyClue` → `"The person who has {left_val} as their {attr} is sitting to the left of the person who has {right_val} as their {attr}."`

```python
compare_solutions(expected: list[dict], llm_solution: list[dict]) -> list[str]
```
Compares by `"Position"` key. Returns a list of mismatch strings (empty = correct). Unknown positions in `llm_solution` are reported as mismatches.

```python
run_sample(model, client, log_path, num_people, num_attrs, sample_num, total_samples, dry_run=False)
```
Writes a log file to `log_path` with these sections in order:
```
######...
# SAMPLE {sample_num}/{total_samples}
# {num_people} people, {num_attrs} attributes
######...

>>> PUZZLE PROMPT
...
>>> RAW API RESPONSE
{json.dumps(response.model_dump(), indent=4)}
>>> LLM OUTPUT TEXT
...
>>> SOLUTION COMPARISON
PASS  (or FAIL: ... )
```
If an exception occurs at any stage, writes `>>> ERROR\n\n{traceback}` and does **not** re-raise. In dry-run mode, stops after logging the prompt.

API calls use: `client.responses.create(model=model, reasoning={"effort": "medium"}, input=prompt)`

```python
main()
```
Parses CLI args: `-p/--min-num-people`, `-P/--max-num-people`, `-a/--min-num-attrs`, `-A/--max-num-attrs`, `-n/--num-samples` (default 1), `-m/--models` (one or more), `--dry-run`.

- Creates an `OpenAI` client pointed at `https://openrouter.ai/api/v1` using `OPEN_ROUTER_TOKEN` env var
- Runs one `run_sample` invocation per `(model, num_people, num_attrs, sample)` combination — all combinations in `[min, max]` inclusive
- Log files go to `logs/{sanitized_model}/p{p}_a{a}_s{s}_{timestamp}.txt`
- All invocations run **in parallel** using `ThreadPoolExecutor(max_workers=min(total, 1000))`

---

## Running the tests

```bash
# All non-live tests (no API token needed)
python -m pytest tests/ -v

# Including live API tests
OPEN_ROUTER_TOKEN=<token> python -m pytest tests/ -v
```
