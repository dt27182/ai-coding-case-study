from dataclasses import dataclass


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


def gen_direct_clues(solution: list[dict]) -> list[DirectClue]:
    clues = []
    for person in solution:
        pos = person["Position"]
        for attr, val in person.items():
            if attr != "Position":
                clues.append(DirectClue(position=pos, attribute=attr, value=val))
    return clues


def gen_attribute_relation_clues(solution: list[dict]) -> list[AttributeRelationClue]:
    clues = []
    for person in solution:
        attrs = {k: v for k, v in person.items() if k != "Position"}
        attr_names = list(attrs.keys())
        for i, attr1 in enumerate(attr_names):
            for attr2 in attr_names:
                if attr1 != attr2:
                    clues.append(AttributeRelationClue(
                        attr1=attr1, val1=attrs[attr1],
                        attr2=attr2, val2=attrs[attr2],
                    ))
    return clues


def gen_adjacency_clues(solution: list[dict]) -> list[AdjacencyClue]:
    # Build position -> person lookup
    by_pos = {person["Position"]: person for person in solution}
    positions = sorted(by_pos.keys())
    attrs = [k for k in solution[0].keys() if k != "Position"]
    clues = []
    for attr in attrs:
        for i in range(len(positions) - 1):
            left_pos = positions[i]
            right_pos = positions[i + 1]
            left_val = by_pos[left_pos][attr]
            right_val = by_pos[right_pos][attr]
            clues.append(AdjacencyClue(attribute=attr, left_val=left_val, right_val=right_val))
    return clues
