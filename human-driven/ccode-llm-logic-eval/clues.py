from dataclasses import dataclass
from itertools import permutations


@dataclass
class DirectClue:
    position: int
    attribute: str
    value: str


@dataclass
class AttributeRelationClue:
    attr1: str
    val1: str
    attr2: str
    val2: str


@dataclass
class AdjacencyClue:
    attribute: str
    left_val: str
    right_val: str


def gen_direct_clues(solution):
    clues = []
    for person in solution:
        pos = person["Position"]
        for attr, val in person.items():
            if attr != "Position":
                clues.append(DirectClue(position=pos, attribute=attr, value=val))
    return clues


def gen_attribute_relation_clues(solution):
    clues = []
    for person in solution:
        attrs = [(k, v) for k, v in person.items() if k != "Position"]
        for (attr1, val1), (attr2, val2) in permutations(attrs, 2):
            clues.append(AttributeRelationClue(attr1=attr1, val1=val1, attr2=attr2, val2=val2))
    return clues


def gen_adjacency_clues(solution):
    clues = []
    sorted_solution = sorted(solution, key=lambda p: p["Position"])
    for i in range(len(sorted_solution) - 1):
        left = sorted_solution[i]
        right = sorted_solution[i + 1]
        for attr in left:
            if attr == "Position":
                continue
            clues.append(AdjacencyClue(attribute=attr, left_val=left[attr], right_val=right[attr]))
    return clues
