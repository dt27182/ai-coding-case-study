from dataclasses import dataclass
from typing import List, Dict, Any

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

def gen_direct_clues(solution: List[Dict[str, Any]]) -> List[DirectClue]:
    clues = []
    for person in solution:
        pos = person["Position"]
        for attr, val in person.items():
            if attr != "Position":
                clues.append(DirectClue(position=pos, attribute=attr, value=val))
    return clues

def gen_attribute_relation_clues(solution: List[Dict[str, Any]]) -> List[AttributeRelationClue]:
    clues = []
    for person in solution:
        attrs = [k for k in person.keys() if k != "Position"]
        for i in range(len(attrs)):
            for j in range(i + 1, len(attrs)):
                attr1 = attrs[i]
                attr2 = attrs[j]
                clues.append(AttributeRelationClue(
                    attr1=attr1, val1=person[attr1],
                    attr2=attr2, val2=person[attr2]
                ))
                # Also add the reverse relation
                clues.append(AttributeRelationClue(
                    attr1=attr2, val1=person[attr2],
                    attr2=attr1, val2=person[attr1]
                ))
    return clues

def gen_adjacency_clues(solution: List[Dict[str, Any]]) -> List[AdjacencyClue]:
    clues = []
    # Sort the solution by position just in case
    sorted_solution = sorted(solution, key=lambda x: x["Position"])
    for i in range(len(sorted_solution) - 1):
        left_person = sorted_solution[i]
        right_person = sorted_solution[i + 1]
        
        attrs = [k for k in left_person.keys() if k != "Position"]
        for attr in attrs:
            clues.append(AdjacencyClue(
                attribute=attr,
                left_val=left_person[attr],
                right_val=right_person[attr]
            ))
    return clues
