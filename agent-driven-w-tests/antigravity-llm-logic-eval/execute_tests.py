import argparse
import datetime
import json
import os
import re
import traceback
from concurrent.futures import ThreadPoolExecutor

from openai import OpenAI
from clues import DirectClue, AttributeRelationClue, AdjacencyClue
from generate_puzzle import generate_puzzle


def puzzle_to_text(puzzle: dict) -> str:
    solution = puzzle['solution']
    clues = puzzle['clues']
    num_people = len(solution)
    
    # 1. Opening
    lines = [f"There are {num_people} people attending a party."]
    
    # 2. Extract possible values
    attributes = {}
    for person in solution:
        for attr, val in person.items():
            if attr != "Position":
                attributes.setdefault(attr, set()).add(val)
                
    for attr, vals in attributes.items():
        v_str = ", ".join(sorted(list(vals)))
        lines.append(f"The possible values for {attr} are: {v_str}.")
        
    # 3. Clues Header
    lines.append("")
    lines.append("Below are a set of clues about each person.")
    
    # 4. Clues
    for clue in clues:
        if isinstance(clue, DirectClue):
            lines.append(f"The person sitting at position {clue.position} has {clue.value} as their {clue.attribute}.")
        elif isinstance(clue, AttributeRelationClue):
            lines.append(f"The person who has {clue.val1} as their {clue.attr1} also has {clue.val2} as their {clue.attr2}.")
        elif isinstance(clue, AdjacencyClue):
            lines.append(f"The person who has {clue.left_val} as their {clue.attribute} is sitting to the left of the person who has {clue.right_val} as their {clue.attribute}.")

    # 5. Instructions
    lines.append("")
    lines.append("Please write the answer as a JSON array demarked within <solution></solution> tags, where each element is a JSON object. Do not include anything else in the output. For example:")
    
    # 6. Example JSON block
    example = []
    for i in range(num_people):
        ex_person = {"Position": i}
        for attr in attributes:
            ex_person[attr] = "..."
        example.append(ex_person)
        
    lines.append("<solution>")
    lines.append(json.dumps(example, indent=2))
    lines.append("</solution>")
    
    return "\n".join(lines)


def compare_solutions(expected: list, llm_solution: list) -> list:
    mismatches = []
    
    expected_dict = {p["Position"]: p for p in expected}
    llm_dict = {p.get("Position"): p for p in llm_solution if "Position" in p}
    
    # Check for all submitted
    for llm_pos, llm_person in llm_dict.items():
        if llm_pos not in expected_dict:
            mismatches.append(f"Unknown Position {llm_pos} found in answer")
            continue
            
        exp_person = expected_dict[llm_pos]
        for attr, val in exp_person.items():
            if attr == "Position":
                continue
            llm_val = llm_person.get(attr)
            if llm_val != val:
                mismatches.append(f"Position {llm_pos} {attr}: Expected {val}, Got {llm_val}")
                
    # Check for missing expected
    for exp_pos, exp_person in expected_dict.items():
        if exp_pos not in llm_dict:
            mismatches.append(f"Position {exp_pos} is entirely missing from the answer")

    return mismatches


def run_sample(model: str, client: OpenAI, log_path: str, num_people: int, num_attrs: int, sample_num: int, total_samples: int, dry_run: bool = False):
    print(f"Starting: model={model}, p={num_people}, a={num_attrs}, sample={sample_num}/{total_samples}")
    try:
        puzzle = generate_puzzle(num_people, num_attrs)
        prompt = puzzle_to_text(puzzle)
        
        # Open file in append safely
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        
        with open(log_path, "w") as f:
            f.write("######################################################################\n")
            f.write(f"# SAMPLE {sample_num}/{total_samples}\n")
            f.write(f"# {num_people} people, {num_attrs} attributes\n")
            f.write("######################################################################\n\n")
            
            f.write(">>> PUZZLE PROMPT\n")
            f.write(prompt)
            f.write("\n")
            
            if dry_run:
                return
                
            response = client.responses.create(
                model=model,
                reasoning={"effort": "none"},
                input=prompt
            )
            
            f.write(">>> RAW API RESPONSE\n\n")
            f.write(json.dumps(response.model_dump(), indent=4))
            f.write("\n>>> LLM OUTPUT TEXT\n")
            output_text = getattr(response, 'output_text', getattr(response, 'output', ''))
            f.write(output_text)
            f.write("\n>>> SOLUTION COMPARISON\n")
            
            # Extract solution block
            solution_match = re.search(r'<solution>\s*(.*?)\s*</solution>', output_text, re.DOTALL)
            if solution_match:
                try:
                    llm_solution = json.loads(solution_match.group(1))
                    mismatches = compare_solutions(puzzle['solution'], llm_solution)
                    if mismatches:
                        f.write("FAIL:\n")
                        for m in mismatches:
                            f.write(f"  - {m}\n")
                        print(f"FAIL: model={model}, p={num_people}, a={num_attrs}, sample={sample_num}/{total_samples}")
                    else:
                        f.write("PASS\n")
                        print(f"PASS: model={model}, p={num_people}, a={num_attrs}, sample={sample_num}/{total_samples}")
                except json.JSONDecodeError:
                    f.write("FAIL: Could not parse JSON array within <solution> tags\n")
                    print(f"FAIL (JSON Error): model={model}, p={num_people}, a={num_attrs}, sample={sample_num}/{total_samples}")
            else:
                f.write("FAIL: No <solution> block found in response\n")
                print(f"FAIL (No Solution): model={model}, p={num_people}, a={num_attrs}, sample={sample_num}/{total_samples}")
                
    except Exception as e:
        with open(log_path, "a") as f:
            f.write(f">>> ERROR\n\n{traceback.format_exc()}")
        print(f"ERROR: model={model}, p={num_people}, a={num_attrs}, sample={sample_num}/{total_samples}")


def main():
    parser = argparse.ArgumentParser(description="LLM Logic Puzzle Evaluator")
    parser.add_argument("-p", "--min-num-people", type=int, required=True)
    parser.add_argument("-P", "--max-num-people", type=int, required=True)
    parser.add_argument("-a", "--min-num-attrs", type=int, required=True)
    parser.add_argument("-A", "--max-num-attrs", type=int, required=True)
    parser.add_argument("-n", "--num-samples", type=int, default=1)
    parser.add_argument("-m", "--models", nargs="+", required=True)
    parser.add_argument("--dry-run", action="store_true")
    
    args = parser.parse_args()
    
    token = os.environ.get("OPEN_ROUTER_TOKEN", "")
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=token
    )
    
    tasks = []
    for model in args.models:
        sanitized_model = model.replace("/", "_")
        for p in range(args.min_num_people, args.max_num_people + 1):
            for a in range(args.min_num_attrs, args.max_num_attrs + 1):
                for s in range(1, args.num_samples + 1):
                    ts = datetime.datetime.now().strftime("%Y%md_%H%M%S")
                    log_path = f"logs/{sanitized_model}/p{p}_a{a}_s{s}_{ts}.txt"
                    tasks.append((model, client, log_path, p, a, s, args.num_samples, args.dry_run))
                    
    with ThreadPoolExecutor(max_workers=min(len(tasks), 1000) if tasks else 1) as executor:
        for t in tasks:
            executor.submit(run_sample, *t)


if __name__ == "__main__":
    main()
