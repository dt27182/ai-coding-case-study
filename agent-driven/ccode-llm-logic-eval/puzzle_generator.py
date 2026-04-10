"""Logic grid puzzle generator using constraint satisfaction."""

import random
from typing import Dict, List, Any

from constraint import Problem, AllDifferentConstraint

from attribute_pools import PERSON_NAMES, ATTRIBUTE_POOLS


def generate_puzzle(num_people: int, num_attributes: int) -> Dict[str, Any]:
    """
    Generate a logic grid puzzle with verified unique solution.

    Args:
        num_people: Number of people (positions) in the puzzle
        num_attributes: Total number of attributes INCLUDING "name"

    Returns:
        Dictionary containing puzzle structure, clues, and solution
    """
    if num_attributes < 1:
        raise ValueError("Must have at least 1 attribute (name)")

    if num_people < 1 or num_people > 20:
        raise ValueError("Number of people must be between 1 and 20")

    # Select attribute categories (excluding "name" which is always included)
    num_extra_attributes = num_attributes - 1
    available_attributes = list(ATTRIBUTE_POOLS.keys())

    if num_extra_attributes > len(available_attributes):
        raise ValueError(
            f"Cannot generate {num_extra_attributes} extra attributes. "
            f"Only {len(available_attributes)} categories available."
        )

    # Randomly select attributes for variety
    selected_attributes = random.sample(available_attributes, num_extra_attributes)

    # Generate attribute values
    attributes = {}
    attributes["name"] = random.sample(PERSON_NAMES, num_people)

    for attr in selected_attributes:
        pool = ATTRIBUTE_POOLS[attr]
        attributes[attr] = random.sample(pool, num_people)

    # Generate a random solution
    solution = generate_random_solution(num_people, attributes)

    # Generate clues
    clues = generate_clues(num_people, attributes, solution)

    # Verify uniqueness with CSP solver
    if verify_unique_solution(num_people, attributes, clues, solution):
        return {
            "num_people": num_people,
            "attributes": attributes,
            "solution": solution,
            "clues": clues
        }
    else:
        raise Exception(f"Failed to generate valid puzzle")



def generate_random_solution(
    num_people: int,
    attribute_values: Dict[str, List[str]]
) -> List[Dict[str, Any]]:
    """Generate a random valid solution from pre-shuffled attribute values."""
    solution = []
    for pos in range(num_people):
        person: Dict[str, Any] = {"Position": pos}
        for attr, values in attribute_values.items():
            person[attr] = values[pos]
        solution.append(person)
    return solution


def generate_clues(
    num_people: int,
    attribute_values: Dict[str, List[str]],
    solution: List[Dict[str, Any]]
) -> List[str]:
    """
    Generate clues that guarantee a unique solution by construction.

    Strategy:
    1. Fix first attribute with positional clues (anchors solution to positions)
    2. Chain remaining attributes via associations (attr1→attr2→attr3...)

    This construction guarantees uniqueness, which is verified by the CSP solver.
    """
    attributes = list(attribute_values.keys())
    clues = []

    # Positional clues for first attribute (anchor)
    anchor_attr = attributes[0]
    for pos in range(num_people):
        value = solution[pos][anchor_attr]
        clues.append(
            f"The person sitting at position {pos} has {value} as their {anchor_attr}."
        )

    # Chain associations: each attribute links to the next
    for i in range(len(attributes) - 1):
        attr1, attr2 = attributes[i], attributes[i + 1]
        for pos in range(num_people):
            value1 = solution[pos][attr1]
            value2 = solution[pos][attr2]
            clues.append(
                f"The person who has {value1} as their {attr1} also has {value2} as their {attr2}."
            )

    return clues


def verify_unique_solution(
    num_people: int,
    attribute_values: Dict[str, List[str]],
    clues: List[str],
    expected_solution: List[Dict[str, Any]]
) -> bool:
    """
    Verify that the given clues lead to a unique solution using CSP.

    Returns:
        True if clues lead to exactly one solution matching expected_solution
    """
    import re

    attributes = list(attribute_values.keys())
    problem = Problem()

    # Create variables: pos_{position}_{attribute}
    for pos in range(num_people):
        for attr in attributes:
            problem.addVariable(f"pos_{pos}_{attr}", attribute_values[attr])

    # Each value appears exactly once per attribute
    for attr in attributes:
        problem.addConstraint(
            AllDifferentConstraint(),
            [f"pos_{pos}_{attr}" for pos in range(num_people)]
        )

    # Add constraints from clues
    for clue in clues:
        # Pattern 1: "The person sitting at position X has Y as their Z."
        match = re.search(r'The person sitting at position (\d+) has (.+?) as their (.+?)\.', clue)
        if match:
            pos, value, attr = int(match.group(1)), match.group(2), match.group(3)
            problem.addConstraint(lambda v, val=value: v == val, (f"pos_{pos}_{attr}",))
            continue

        # Pattern 2: "The person who has X as their Y also has A as their B."
        match = re.search(r'The person who has (.+?) as their (.+?) also has (.+?) as their (.+?)\.', clue)
        if match:
            value1, attr1, value2, attr2 = match.groups()
            for pos in range(num_people):
                problem.addConstraint(
                    lambda v1, v2, val1=value1, val2=value2: v1 != val1 or v2 == val2,
                    (f"pos_{pos}_{attr1}", f"pos_{pos}_{attr2}")
                )
            continue


    # Get all solutions and verify
    solutions = problem.getSolutions()
    if len(solutions) != 1:
        return False

    # Check solution matches expected
    sol = solutions[0]
    for pos in range(num_people):
        for attr in attributes:
            if sol[f"pos_{pos}_{attr}"] != expected_solution[pos][attr]:
                return False
    return True


def main():
    """Demonstrate puzzle generation."""
    import json

    print("Generating a 20-person puzzle with 20 attributes (name + 19 others)...")
    print("=" * 60)

    puzzle = generate_puzzle(num_people=20, num_attributes=20)

    print(f"\nNumber of people: {puzzle['num_people']}")
    print(f"Attributes: {list(puzzle['attributes'].keys())}")

    print("\nPossible values:")
    for attr, values in puzzle['attributes'].items():
        print(f"  {attr}: {values}")

    print(f"\nClues ({len(puzzle['clues'])}):")
    for i, clue in enumerate(puzzle['clues'], 1):
        print(f"  {i}. {clue}")

    print("\nSolution:")
    print(json.dumps(puzzle['solution'], indent=2))

    print("\n" + "=" * 60)
    print("Puzzle generated successfully with verified unique solution!")


if __name__ == "__main__":
    main()
