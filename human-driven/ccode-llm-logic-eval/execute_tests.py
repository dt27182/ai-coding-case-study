import argparse
import json
import os
import re
import random
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from openai import OpenAI

from clues import AdjacencyClue, AttributeRelationClue, DirectClue
from generate_puzzle import generate_puzzle


def _join_attrs(attrs):
    if len(attrs) == 1:
        return attrs[0]
    if len(attrs) == 2:
        return f"{attrs[0]} and {attrs[1]}"
    return ", ".join(attrs[:-1]) + f", and {attrs[-1]}"


def puzzle_to_text(puzzle):
    solution = puzzle['solution']
    clues = puzzle['clues']
    num_people = len(solution)
    attr_names = [k for k in solution[0] if k != 'Position']

    lines = []

    lines.append(
        f"There are {num_people} people attending a party. Everyone is sitting in a row. "
        f"The left most seat will be referred to as position 0, the next seat to the right "
        f"will be referred to as position 1 and so on. "
        f"Each person has a {_join_attrs(attr_names)}."
    )
    lines.append("")

    for attr in attr_names:
        values = [person[attr] for person in solution]
        random.shuffle(values)
        lines.append(f"The possible values for {attr} are: {', '.join(str(v) for v in values)}")

    lines.append("")
    lines.append("Below are a set of clues about each person.")
    lines.append("")

    clue_texts = []
    for clue in clues:
        if isinstance(clue, DirectClue):
            clue_texts.append(
                f"The person sitting at position {clue.position} has {clue.value} as their {clue.attribute}."
            )
        elif isinstance(clue, AttributeRelationClue):
            clue_texts.append(
                f"The person who has {clue.val1} as their {clue.attr1} also has {clue.val2} as their {clue.attr2}."
            )
        elif isinstance(clue, AdjacencyClue):
            clue_texts.append(
                f"The person who has {clue.left_val} as their {clue.attribute} is sitting to the left of "
                f"the person who has {clue.right_val} as their {clue.attribute}."
            )
    lines.extend(clue_texts)

    lines.append("")
    lines.append(f"Can you figure out what each person's {_join_attrs(attr_names)} are?")
    lines.append("")
    lines.append(
        "Please write the answer as a JSON array demarked within <solution></solution> tags, "
        "where each element is a JSON object. Do not include anything else in the output. For example:"
    )

    example = [{"Position": i, **{attr: "X" for attr in attr_names}} for i in range(num_people)]
    lines.append(f"<solution>\n{json.dumps(example, indent=4)}\n</solution>")

    return "\n".join(lines)


def _parse_llm_solution(output_text):
    match = re.search(r'<solution>(.*?)</solution>', output_text, re.DOTALL)
    if not match:
        return None
    return json.loads(match.group(1).strip())


def compare_solutions(expected, llm_solution):
    expected_by_pos = {p['Position']: p for p in expected}
    mismatches = []
    for llm_person in llm_solution:
        pos = llm_person.get('Position')
        expected_person = expected_by_pos.get(pos)
        if expected_person is None:
            mismatches.append(f"  Position {pos}: not in expected solution")
            continue
        for attr, val in llm_person.items():
            if attr == 'Position':
                continue
            if str(val) != str(expected_person.get(attr)):
                mismatches.append(f"  Position {pos}, {attr}: expected '{expected_person.get(attr)}', got '{val}'")
    return mismatches


def run_sample(model, client, log_path, num_people, num_attrs, sample_num, total_samples, dry_run=False):
    with open(log_path, "w") as log:
        log.write(f"\n{'#'*60}\n")
        log.write(f"# SAMPLE {sample_num}/{total_samples}\n")
        log.write(f"# {num_people} people, {num_attrs} attributes\n")
        log.write(f"{'#'*60}\n")

        try:
            print(f"\nSample {sample_num}/{total_samples} — generating puzzle ({num_people}p x {num_attrs}a)...")
            puzzle = generate_puzzle(num_people, num_attrs)
            prompt = puzzle_to_text(puzzle)

            log.write("\n>>> PUZZLE PROMPT\n\n")
            log.write(prompt + "\n")
            log.flush()

            if dry_run:
                print("Dry run — skipping API call")
                log.write("\n>>> DRY RUN — API call skipped\n")
                return

            print("Sending to LLM...")
            response = client.responses.create(
                model=model,
                reasoning={"effort": "medium"},
                input=prompt,
            )

            log.write("\n>>> RAW API RESPONSE\n\n")
            log.write(json.dumps(response.model_dump(), indent=4) + "\n")

            log.write("\n>>> LLM OUTPUT TEXT\n\n")
            log.write(response.output_text + "\n")

            llm_solution = _parse_llm_solution(response.output_text)
            log.write("\n>>> SOLUTION COMPARISON\n\n")
            if llm_solution is None:
                log.write("FAIL: could not parse <solution> from response\n")
            else:
                mismatches = compare_solutions(puzzle['solution'], llm_solution)
                if mismatches:
                    log.write("FAIL:\n" + "\n".join(mismatches) + "\n")
                else:
                    log.write("PASS\n")

        except Exception:
            log.write("\n>>> ERROR\n\n")
            log.write(traceback.format_exc() + "\n")
            log.flush()
            print(f"Error on sample {sample_num} — written to log")

    return log_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--min-num-people", type=int, required=True)
    parser.add_argument("-P", "--max-num-people", type=int, required=True)
    parser.add_argument("-a", "--min-num-attrs", type=int, required=True)
    parser.add_argument("-A", "--max-num-attrs", type=int, required=True)
    parser.add_argument("-n", "--num-samples", type=int, default=1)
    parser.add_argument("-m", "--models", nargs="+", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    client = OpenAI(
        api_key=os.environ['OPEN_ROUTER_TOKEN'],
        base_url="https://openrouter.ai/api/v1",
    )

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    configs = [
        (num_people, num_attrs)
        for num_people in range(args.min_num_people, args.max_num_people + 1)
        for num_attrs in range(args.min_num_attrs, args.max_num_attrs + 1)
    ]

    invocations = []
    for model in args.models:
        model_dir = re.sub(r'[^a-zA-Z0-9\-]', '_', model)
        log_dir = os.path.join("logs", model_dir)
        os.makedirs(log_dir, exist_ok=True)
        for num_people, num_attrs in configs:
            for s in range(1, args.num_samples + 1):
                log_path = os.path.join(log_dir, f"p{num_people}_a{num_attrs}_s{s}_{timestamp}.txt")
                invocations.append((model, log_path, num_people, num_attrs))

    total = len(invocations)
    with ThreadPoolExecutor(max_workers=min(total, 1000)) as executor:
        futures = [
            executor.submit(run_sample, model, client, log_path, num_people, num_attrs, i + 1, total, args.dry_run)
            for i, (model, log_path, num_people, num_attrs) in enumerate(invocations)
        ]
        for future in as_completed(futures):
            print(f"Results saved to {future.result()}")


if __name__ == "__main__":
    main()