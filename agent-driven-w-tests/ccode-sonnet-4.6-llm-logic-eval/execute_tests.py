import argparse
import json
import os
import re
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from openai import OpenAI

from generate_puzzle import generate_puzzle
from clues import DirectClue, AttributeRelationClue, AdjacencyClue


def puzzle_to_text(puzzle: dict) -> str:
    solution = puzzle["solution"]
    clues = puzzle["clues"]
    num_people = len(solution)

    # Collect attribute names and their possible values from solution
    attrs = [k for k in solution[0].keys() if k != "Position"]
    attr_values: dict[str, list] = {attr: [] for attr in attrs}
    for person in sorted(solution, key=lambda p: p["Position"]):
        for attr in attrs:
            attr_values[attr].append(person[attr])

    lines = []
    lines.append(f"There are {num_people} people attending a party.")
    lines.append("")
    for attr in attrs:
        vals_str = ", ".join(attr_values[attr])
        lines.append(f"The possible values for {attr} are: {vals_str}")
    lines.append("")
    lines.append("Below are a set of clues about each person.")
    lines.append("")

    for clue in clues:
        if isinstance(clue, DirectClue):
            lines.append(
                f"The person sitting at position {clue.position} has {clue.value} as their {clue.attribute}."
            )
        elif isinstance(clue, AttributeRelationClue):
            lines.append(
                f"The person who has {clue.val1} as their {clue.attr1} also has {clue.val2} as their {clue.attr2}."
            )
        elif isinstance(clue, AdjacencyClue):
            lines.append(
                f"The person who has {clue.left_val} as their {clue.attribute} is sitting to the left of "
                f"the person who has {clue.right_val} as their {clue.attribute}."
            )

    lines.append("")
    lines.append(
        "Please write the answer as a JSON array demarked within <solution></solution> tags, "
        "where each element is a JSON object. Do not include anything else in the output. For example:"
    )

    # Build example solution array
    example = []
    for i in range(num_people):
        item: dict = {"Position": i}
        for attr in attrs:
            item[attr] = f"Example{attr}{i}"
        example.append(item)
    lines.append(f"<solution>{json.dumps(example)}</solution>")

    return "\n".join(lines)


def compare_solutions(expected: list[dict], llm_solution: list[dict]) -> list[str]:
    expected_by_pos = {p["Position"]: p for p in expected}
    llm_by_pos = {p["Position"]: p for p in llm_solution}

    mismatches = []

    for pos, exp_person in expected_by_pos.items():
        if pos not in llm_by_pos:
            mismatches.append(f"Position {pos}: missing from LLM solution")
            continue
        llm_person = llm_by_pos[pos]
        for key, exp_val in exp_person.items():
            llm_val = llm_person.get(key)
            if llm_val != exp_val:
                mismatches.append(
                    f"Position {pos}: {key} expected {exp_val!r}, got {llm_val!r}"
                )

    for pos in llm_by_pos:
        if pos not in expected_by_pos:
            mismatches.append(f"Position {pos}: unknown position in LLM solution")

    return mismatches


def run_sample(
    model: str,
    client,
    log_path: str,
    num_people: int,
    num_attrs: int,
    sample_num: int,
    total_samples: int,
    dry_run: bool = False,
) -> None:
    sep = "#" * 60
    header = (
        f"{sep}\n"
        f"# SAMPLE {sample_num}/{total_samples}\n"
        f"# {num_people} people, {num_attrs} attributes\n"
        f"{sep}"
    )

    os.makedirs(os.path.dirname(log_path), exist_ok=True) if os.path.dirname(log_path) else None

    with open(log_path, "w") as f:
        f.write(header + "\n\n")

        try:
            puzzle = generate_puzzle(num_people, num_attrs)
            prompt = puzzle_to_text(puzzle)
            f.write(">>> PUZZLE PROMPT\n")
            f.write(prompt + "\n")

            if dry_run:
                return

            response = client.responses.create(
                model=model,
                reasoning={"effort": "medium"},
                input=prompt,
            )

            f.write(">>> RAW API RESPONSE\n\n")
            f.write(json.dumps(response.model_dump(), indent=4) + "\n")

            output_text = response.output_text
            f.write(">>> LLM OUTPUT TEXT\n")
            f.write(output_text + "\n")

            # Extract solution from <solution>...</solution> tags
            match = re.search(r"<solution>(.*?)</solution>", output_text, re.DOTALL)
            if match:
                llm_solution = json.loads(match.group(1).strip())
            else:
                llm_solution = []

            mismatches = compare_solutions(puzzle["solution"], llm_solution)

            f.write(">>> SOLUTION COMPARISON\n")
            if mismatches:
                f.write("FAIL: " + "; ".join(mismatches) + "\n")
            else:
                f.write("PASS\n")

        except Exception:
            f.write(">>> ERROR\n\n")
            f.write(traceback.format_exc() + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run LLM logic puzzle evaluation")
    parser.add_argument("-p", "--min-num-people", type=int, required=True)
    parser.add_argument("-P", "--max-num-people", type=int, required=True)
    parser.add_argument("-a", "--min-num-attrs", type=int, required=True)
    parser.add_argument("-A", "--max-num-attrs", type=int, required=True)
    parser.add_argument("-n", "--num-samples", type=int, default=1)
    parser.add_argument("-m", "--models", nargs="+", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    client = OpenAI(
        api_key=os.environ["OPEN_ROUTER_TOKEN"],
        base_url="https://openrouter.ai/api/v1",
    )

    tasks = []
    for model in args.models:
        sanitized_model = re.sub(r"[^\w\-.]", "_", model)
        for num_people in range(args.min_num_people, args.max_num_people + 1):
            for num_attrs in range(args.min_num_attrs, args.max_num_attrs + 1):
                for sample_num in range(1, args.num_samples + 1):
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    log_path = os.path.join(
                        "logs",
                        sanitized_model,
                        f"p{num_people}_a{num_attrs}_s{sample_num}_{timestamp}.txt",
                    )
                    tasks.append((model, client, log_path, num_people, num_attrs, sample_num, args.num_samples, args.dry_run))

    total = len(tasks)
    with ThreadPoolExecutor(max_workers=min(total, 1000)) as executor:
        futures = [
            executor.submit(run_sample, *task)
            for task in tasks
        ]
        for future in futures:
            future.result()


if __name__ == "__main__":
    main()
