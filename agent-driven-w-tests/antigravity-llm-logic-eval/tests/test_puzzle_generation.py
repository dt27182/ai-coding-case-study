import copy
import sys
import os
import threading

import pytest
from constraint import AllDifferentConstraint, Problem

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from clues import AdjacencyClue, AttributeRelationClue, DirectClue
from clues import gen_adjacency_clues, gen_attribute_relation_clues, gen_direct_clues
from generate_puzzle import generate_puzzle


# ---------------------------------------------------------------------------
# Independent CSP helpers (copies — not imported from generate_puzzle.py)
# ---------------------------------------------------------------------------

def _test_build_base_csp(solution):
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


def _test_has_unique_solution(base_problem, clues):
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


# ---------------------------------------------------------------------------
# Property 1: Generate puzzles up to 20x20 within 15 seconds
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("num_people,num_attrs", [(10, 10), (15, 15), (20, 20)])
def test_generate_puzzle_large_sizes_within_timeout(num_people, num_attrs):
    TIMEOUT = 15
    result: list = [None]

    def run():
        result[0] = generate_puzzle(num_people, num_attrs)

    t = threading.Thread(target=run, daemon=True)
    t.start()
    t.join(timeout=TIMEOUT)
    if t.is_alive():
        pytest.fail(f"generate_puzzle({num_people}, {num_attrs}) timed out after {TIMEOUT}s")

    assert result[0] is not None
    puzzle = result[0]
    solution = puzzle['solution']
    assert len(solution) == num_people
    assert len(solution[0]) - 1 == num_attrs  # -1 for 'Position'


# ---------------------------------------------------------------------------
# Property 2: Reasonable distribution of all 3 clue types
# ---------------------------------------------------------------------------

SMALL_SOLUTION = [
    {"Position": 0, "Name": "Alice", "Job": "Doctor", "Color": "Red"},
    {"Position": 1, "Name": "Bob",   "Job": "Farmer", "Color": "Blue"},
    {"Position": 2, "Name": "Carol", "Job": "Pilot",  "Color": "Green"},
]


def test_gen_direct_clues_nonempty():
    assert len(gen_direct_clues(SMALL_SOLUTION)) > 0


def test_gen_attribute_relation_clues_nonempty():
    assert len(gen_attribute_relation_clues(SMALL_SOLUTION)) > 0


def test_gen_adjacency_clues_nonempty():
    assert len(gen_adjacency_clues(SMALL_SOLUTION)) > 0


# Per-config expected distribution bounds (averaged over NUM_SAMPLES runs).
# Derived from theoretical potential-clue ratios and empirical observations.
# Potential ratios: direct=N*M, relation=N*M*(M-1), adjacency=(N-1)*M out of total.
# Bounds are empirical mean ± ~3 std deviations of the mean for NUM_SAMPLES=5.
_DISTRIBUTION_CASES = [
    # (num_people, num_attrs, direct_bounds, relation_bounds, adjacency_bounds)
    (3,  3,  (15, 45), (40, 72), (2, 28)),
    (5,  5,  (10, 30), (60, 80), (2, 20)),
    (8,  8,  ( 4, 22), (65, 88), (2, 18)),
    (10, 10, ( 2, 18), (73, 92), (2, 15)),
    (20, 20, ( 1, 12), (83, 97), (1, 10)),
]


@pytest.mark.parametrize(
    "num_people,num_attrs,direct_bounds,relation_bounds,adjacency_bounds",
    _DISTRIBUTION_CASES,
)
def test_clue_type_distribution(num_people, num_attrs, direct_bounds, relation_bounds, adjacency_bounds):
    NUM_SAMPLES = 5
    totals = {'direct': 0, 'relation': 0, 'adjacency': 0, 'total': 0}
    for _ in range(NUM_SAMPLES):
        puzzle = generate_puzzle(num_people, num_attrs)
        clues = puzzle['clues']
        totals['direct'] += sum(1 for c in clues if isinstance(c, DirectClue))
        totals['relation'] += sum(1 for c in clues if isinstance(c, AttributeRelationClue))
        totals['adjacency'] += sum(1 for c in clues if isinstance(c, AdjacencyClue))
        totals['total'] += len(clues)

    total = totals['total']
    direct_pct = 100 * totals['direct'] / total
    relation_pct = 100 * totals['relation'] / total
    adjacency_pct = 100 * totals['adjacency'] / total

    lo, hi = direct_bounds
    assert lo <= direct_pct <= hi, f"DirectClue at {direct_pct:.1f}% — expected {lo}–{hi}%"
    lo, hi = relation_bounds
    assert lo <= relation_pct <= hi, f"AttributeRelationClue at {relation_pct:.1f}% — expected {lo}–{hi}%"
    lo, hi = adjacency_bounds
    assert lo <= adjacency_pct <= hi, f"AdjacencyClue at {adjacency_pct:.1f}% — expected {lo}–{hi}%"


# ---------------------------------------------------------------------------
# Property 3: Reasonable clue count (not too far above minimum)
# ---------------------------------------------------------------------------

# Bounds derived empirically from 20 samples per config.
# Lower bound = observed minimum; upper bound = observed maximum + ~20% buffer.
_CLUE_COUNT_CASES = [
    # (num_people, num_attrs, min_clues, max_clues)
    (3,  3,   12,   14),
    (5,  5,   35,   50),
    (8,  8,   89,  150),
    (10, 10,  140,  250),
    (15, 15,  517,  650),
    (20, 20, 1240, 1300),
]


@pytest.mark.parametrize("num_people,num_attrs,min_clues,max_clues", _CLUE_COUNT_CASES)
def test_clue_count_within_reasonable_bounds(num_people, num_attrs, min_clues, max_clues):
    puzzle = generate_puzzle(num_people, num_attrs)
    num_clues = puzzle['num_clues']
    assert num_clues >= min_clues, (
        f"{num_people}x{num_attrs}: got {num_clues} clues, expected >= {min_clues}"
    )
    assert num_clues <= max_clues, (
        f"{num_people}x{num_attrs}: got {num_clues} clues, expected <= {max_clues}"
    )


# ---------------------------------------------------------------------------
# Property 4: Puzzles have a unique solution (independent CSP verification)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("num_people,num_attrs", [
    (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (8, 8), (10, 10), (15, 15), (20, 20)
])
def test_puzzle_has_unique_solution(num_people, num_attrs):
    for _ in range(2):
        puzzle = generate_puzzle(num_people, num_attrs)
        base = _test_build_base_csp(puzzle['solution'])
        assert _test_has_unique_solution(base, puzzle['clues']), (
            f"Puzzle ({num_people}x{num_attrs}) does not have a unique solution"
        )
