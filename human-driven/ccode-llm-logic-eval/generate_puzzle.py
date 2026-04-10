import copy
import random

from constraint import AllDifferentConstraint, Problem

from attribute_pools import ATTRIBUTE_POOLS
from clues import *


def generate_puzzle(num_people: int, num_attributes: int):
    solution = select_solution(num_people, num_attributes)
    clues = gen_clues(solution)
    return {'solution': solution, 'clues': clues, 'num_clues': len(clues)}

def select_solution(num_people: int, num_attributes: int) -> list[dict]:
    if num_attributes > len(ATTRIBUTE_POOLS):
        raise ValueError(f"num_attributes cannot exceed {len(ATTRIBUTE_POOLS)}")

    chosen_categories = random.sample(list(ATTRIBUTE_POOLS.keys()), num_attributes)

    people: list[dict[str, int | str]] = [{"Position": i} for i in range(num_people)]
    for category in chosen_categories:
        values = random.sample(ATTRIBUTE_POOLS[category], num_people)
        for person, value in zip(people, values):
            person[category] = value

    return people

def gen_clues(solution):
    num_people = len(solution)
    num_attributes = len(solution[0]) - 1  # exclude Position

    potential_clues = gen_adjacency_clues(solution) + gen_direct_clues(solution) + gen_attribute_relation_clues(solution)
    random.shuffle(potential_clues)

    difficulty = max(num_people, num_attributes) ** 2
    if difficulty <= 100:
        num_initial_clues = min(int(num_people * num_attributes * 1.4), len(potential_clues))
    elif difficulty < 225:
        num_initial_clues = min(int(difficulty * 2), len(potential_clues))
    elif difficulty < 289:
        num_initial_clues = min(int(difficulty * 2.3), len(potential_clues))
    else:
        num_initial_clues = min(int(difficulty * 3.1), len(potential_clues))

    num_clues_per_iteration = max(1, random.randint(
        int(num_people * num_attributes * 0.06) - 1,
        int(num_people * num_attributes * 0.06) + 1)
    )

    base_problem = _build_base_csp(solution)

    accepted_clues = potential_clues[:num_initial_clues]
    if _has_unique_solution(base_problem, accepted_clues):
        return accepted_clues

    idx = num_initial_clues
    while idx < len(potential_clues):
        idx = min(idx + num_clues_per_iteration, len(potential_clues))
        accepted_clues = potential_clues[:idx]
        if _has_unique_solution(base_problem, accepted_clues):
            return accepted_clues

    return accepted_clues

def _build_base_csp(solution):
    problem = Problem()
    positions = list(range(len(solution)))

    attrs = {}
    for person in solution:
        for attr, val in person.items():
            if attr != "Position":
                attrs.setdefault(attr, []).append(val)

    for attr, vals in attrs.items():
        for val in vals:
            problem.addVariable((attr, val), positions)
        problem.addConstraint(AllDifferentConstraint(), [(attr, v) for v in vals])

    return problem


def _has_unique_solution(base_problem, clues):
    problem = copy.deepcopy(base_problem)

    for clue in clues:
        if isinstance(clue, DirectClue):
            p = clue.position
            problem.addConstraint(lambda pos, p=p: pos == p, [(clue.attribute, clue.value)])
        elif isinstance(clue, AttributeRelationClue):
            problem.addConstraint(lambda p1, p2: p1 == p2, [(clue.attr1, clue.val1), (clue.attr2, clue.val2)])
        elif isinstance(clue, AdjacencyClue):
            problem.addConstraint(lambda pl, pr: pl + 1 == pr, [(clue.attribute, clue.left_val), (clue.attribute, clue.right_val)])

    it = problem.getSolutionIter()
    first = next(it, None)
    if first is None:
        return False
    return next(it, None) is None


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--num-people", type=int, required=True)
    parser.add_argument("-a", "--num-attributes", type=int, required=True)
    args = parser.parse_args()
    puzzle = generate_puzzle(num_people=args.num_people, num_attributes=args.num_attributes)
    print(puzzle)


if __name__ == "__main__":
    main()
