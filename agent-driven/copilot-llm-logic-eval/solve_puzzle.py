from constraint import Problem, AllDifferentConstraint
from typing import Dict, List, Callable, Optional, Any


class ZebraPuzzleSolver:
    def __init__(self, num_people: int, attributes: Dict[str, List[str]]) -> None:
        self.num_people: int = num_people
        self.attributes: Dict[str, List[str]] = attributes
        self.problem: Problem = Problem()
        
    def add_variables(self) -> None:
        for attr_name, values in self.attributes.items():
            for value in values:
                self.problem.addVariable(f"{attr_name}_{value}", range(self.num_people))
        
        for attr_name in self.attributes.keys():
            variables = [f"{attr_name}_{val}" for val in self.attributes[attr_name]]
            self.problem.addConstraint(AllDifferentConstraint(), variables)
    
    def add_constraint(self, constraint_func: Callable, variables: List[str]) -> None:
        self.problem.addConstraint(constraint_func, variables)
    
    def solve(self) -> Optional[Dict[str, Dict[str, str]]]:
        solutions = self.problem.getSolutions()
        if not solutions:
            return None
        
        solution = solutions[0]
        return self._format_solution(solution)
    
    def is_solvable(self) -> bool:
        return len(self.problem.getSolutions()) > 0
    
    def has_unique_solution(self) -> bool:
        solutions = self.problem.getSolutions()
        return len(solutions) == 1
    
    def _format_solution(self, solution: Dict[str, int]) -> Dict[str, Dict[str, str]]:
        result: Dict[str, Dict[str, str]] = {}
        for person_id in range(self.num_people):
            person_key = f"person_{person_id}"
            result[person_key] = {}
            
            for attr_name, values in self.attributes.items():
                for value in values:
                    var_name = f"{attr_name}_{value}"
                    if solution[var_name] == person_id:
                        result[person_key][attr_name] = value
        
        return result


def create_solver_with_clues(num_people: int, attributes: Dict[str, List[str]], clues: List[Dict[str, Any]]) -> ZebraPuzzleSolver:
    solver = ZebraPuzzleSolver(num_people, attributes)
    solver.add_variables()
    
    for clue in clues:
        clue_type = clue['type']
        
        if clue_type == 'same_person':
            attr1, val1 = clue['attr1'], clue['val1']
            attr2, val2 = clue['attr2'], clue['val2']
            var1 = f"{attr1}_{val1}"
            var2 = f"{attr2}_{val2}"
            solver.add_constraint(lambda a, b: a == b, [var1, var2])
        
        elif clue_type == 'left_of':
            attr1, val1 = clue['attr1'], clue['val1']
            attr2, val2 = clue['attr2'], clue['val2']
            var1 = f"{attr1}_{val1}"
            var2 = f"{attr2}_{val2}"
            solver.add_constraint(lambda a, b: b == a + 1, [var1, var2])
        
        elif clue_type == 'position':
            attr, val = clue['attr'], clue['val']
            position = clue['position']
            var = f"{attr}_{val}"
            solver.add_constraint(lambda a, p=position: a == p, [var])
    
    return solver
