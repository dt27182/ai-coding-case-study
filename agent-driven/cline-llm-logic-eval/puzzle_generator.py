"""
Logic Grid Puzzle Generator
Generates Einstein-style logic puzzles with configurable people and categories.
Uses CSP solver to verify puzzles have a unique solution.
"""

import random
import json
from typing import Dict, List, Tuple, Set, Optional, Union
from dataclasses import dataclass
from constraint import Problem, AllDifferentConstraint

from category_data import CATEGORY_NAMES, VALUE_POOLS


@dataclass
class RelationshipClue:
    """Clue: person with val1 for cat1 also has val2 for cat2."""
    category1: str
    value1: str
    category2: str
    value2: str
    
    def to_text(self) -> str:
        return f"The person who has {self.value1} as their {self.category1} also has {self.value2} as their {self.category2}."


@dataclass
class PositionClue:
    """Clue: person at position X has value for category."""
    position: int
    category: str
    value: str
    
    def to_text(self) -> str:
        return f"The person sitting at position {self.position} has {self.value} as their {self.category}."


@dataclass
class LeftOfClue:
    """Clue: person with val1 for cat1 is directly left (adjacent) to person with val2 for cat2."""
    category1: str
    value1: str
    category2: str
    value2: str
    
    def to_text(self) -> str:
        return f"The person who has {self.value1} as their {self.category1} is sitting directly to the left of the person who has {self.value2} as their {self.category2}."


# Type alias for any clue type
Clue = Union[RelationshipClue, PositionClue, LeftOfClue]


class LogicPuzzle:
    """Represents a logic grid puzzle with solution."""
    
    def __init__(self, num_people: int, categories: Dict[str, List[str]]):
        """
        Initialize a logic puzzle.
        
        Args:
            num_people: Number of people in the puzzle (1-20)
            categories: Dict mapping category names to lists of possible values
                       e.g., {"name": ["Alice", "Bob"], "color": ["Red", "Blue"]}
        """
        self.num_people = num_people
        self.categories = categories
        self.solution: Optional[List[Dict[str, Union[int, str]]]] = None
        self.clues: List[Clue] = []
        self.max_attempts = 50  # Max attempts to find valid clue set
        
    def generate(self, max_retries: int = 10) -> bool:
        """
        Generate a random valid solution and create clues that guarantee uniqueness.
        
        Args:
            max_retries: Maximum number of complete regeneration attempts
            
        Returns:
            True if puzzle was successfully generated with unique solution
        """
        for attempt in range(max_retries):
            # Create a random solution
            self.solution = self._generate_solution()
            
            # Try to generate clues that result in unique solution
            if self._generate_verified_clues():
                return True
        
        # If we couldn't generate valid clues after retries, keep the last attempt
        return False
    
    def _generate_solution(self) -> List[Dict[str, Union[int, str]]]:
        """
        Generate a random valid solution.
        
        Returns:
            List of dicts, where each dict represents a person with their attributes
        """
        solution = []
        
        for position in range(self.num_people):
            person: Dict[str, Union[int, str]] = {"Position": position}
            solution.append(person)
        
        # Assign each category's values to people
        for category, values in self.categories.items():
            # Randomly shuffle and assign values
            shuffled_values = values.copy()
            random.shuffle(shuffled_values)
            
            for position, value in enumerate(shuffled_values):
                solution[position][category] = value
        
        return solution
    
    def _generate_verified_clues(self) -> bool:
        """
        Generate clues and verify they result in a unique solution.
        Uses difficulty-based initial clue selection for better performance.
        Guaranteed to succeed by eventually adding all clues if needed.
        
        Returns:
            True if clues result in unique solution matching our solution
        """
        categories_list = list(self.categories.keys())
        
        # Step 1: Generate ALL possible clues of each type
        
        # Relationship clues: link all category pairs
        relationship_clues = []
        for i in range(len(categories_list)):
            for j in range(i + 1, len(categories_list)):
                cat1, cat2 = categories_list[i], categories_list[j]
                for person in self.solution:
                    val1 = str(person[cat1])
                    val2 = str(person[cat2])
                    clue = RelationshipClue(
                        category1=cat1,
                        value1=val1,
                        category2=cat2,
                        value2=val2
                    )
                    relationship_clues.append(clue)
        
        # Position clues: specify attributes at each position
        position_clues = []
        for pos in range(self.num_people):
            person = self.solution[pos]
            for category in categories_list:
                value = str(person[category])
                clue = PositionClue(
                    position=pos,
                    category=category,
                    value=value
                )
                position_clues.append(clue)
        
        # Adjacency clues: specify relationships between adjacent positions
        adjacency_clues = []
        if self.num_people >= 2:
            for pos1 in range(self.num_people - 1):
                pos2 = pos1 + 1
                person1 = self.solution[pos1]
                person2 = self.solution[pos2]
                
                for cat1 in categories_list:
                    for cat2 in categories_list:
                        val1 = str(person1[cat1])
                        val2 = str(person2[cat2])
                        clue = LeftOfClue(
                            category1=cat1,
                            value1=val1,
                            category2=cat2,
                            value2=val2
                        )
                        adjacency_clues.append(clue)
        
        # Step 2: Shuffle all clues together for fair distribution
        all_clues = relationship_clues + position_clues + adjacency_clues
        random.shuffle(all_clues)
        
        # Step 3: Calculate initial number of clues based on difficulty
        num_people = self.num_people
        num_attributes = len(self.categories)
        difficulty = max(num_people, num_attributes) ** 2
        
        if difficulty <= 100:
            num_initial_clues = min(int(num_people * num_attributes * 1.4), len(all_clues))
        elif difficulty < 225:
            num_initial_clues = min(int(difficulty * 2), len(all_clues))
        elif difficulty < 289:
            num_initial_clues = min(int(difficulty * 2.3), len(all_clues))
        else:
            num_initial_clues = min(int(difficulty * 3.1), len(all_clues))
        
        # Step 4: Create CSP problem once and reuse it
        problem = Problem()
        
        # Add variables once
        for pos in range(self.num_people):
            for category in categories_list:
                var_name = f"pos{pos}_{category}"
                problem.addVariable(var_name, self.categories[category])
        
        # Add AllDifferent constraints once
        for category in categories_list:
            category_vars = [f"pos{pos}_{category}" for pos in range(self.num_people)]
            problem.addConstraint(AllDifferentConstraint(), category_vars)
        
        # Step 5: Add initial batch of clues
        current_clues: List[Clue] = all_clues[:num_initial_clues]
        for clue in current_clues:
            self._add_clue_constraint(problem, clue)
        
        # Check if initial clues produce unique solution (with early termination)
        solutions = self._solve_problem_limited(problem, max_solutions=2)
        
        if len(solutions) == 1 and self._solutions_match(solutions[0], self.solution):
            # Found unique solution! Shuffle clues for variety in presentation
            random.shuffle(current_clues)
            self.clues = current_clues
            return True
        
        # Step 6: If not unique, add remaining clues in batches
        # Calculate batch size based on puzzle difficulty (with randomness)
        base_batch_size = int(num_people * num_attributes * 0.06)
        num_clues_per_iteration = max(1, random.randint(base_batch_size - 1, base_batch_size + 1))
        
        remaining_clues = all_clues[num_initial_clues:]
        
        i = 0
        while i < len(remaining_clues):
            # Add next batch of clues to the existing problem
            batch = remaining_clues[i:i+num_clues_per_iteration]
            for clue in batch:
                self._add_clue_constraint(problem, clue)
            current_clues.extend(batch)
            i += num_clues_per_iteration
            
            # Check if current clues produce unique solution (with early termination)
            solutions = self._solve_problem_limited(problem, max_solutions=2)
            
            if len(solutions) == 1 and self._solutions_match(solutions[0], self.solution):
                # Found unique solution! Shuffle clues for variety in presentation
                random.shuffle(current_clues)
                self.clues = current_clues
                return True
        
        # Step 7: If we've added all clues, we should have unique solution
        # This is guaranteed to work (all clues together must specify unique solution)
        self.clues = current_clues
        return True
    
    def _generate_clues_candidate(self) -> List[Clue]:
        """
        Generate a candidate set of clues.
        Uses multiple clue types for variety.
        
        Returns:
            List of structured clue objects
        """
        clues: List[Clue] = []
        categories_list = list(self.categories.keys())
        
        # Strategy: Generate different types of clues
        # Type 1: Relationship clues (person with A has B)
        # Type 2: Direct position clues (person at position X has Y)
        # Type 3: Relative position clues (person with A is left of person with B)
        
        # Add relationship clues for all category pairs
        for i in range(len(categories_list)):
            for j in range(i + 1, len(categories_list)):
                cat1, cat2 = categories_list[i], categories_list[j]
                
                # For each person, create a clue relating these two categories
                for person in self.solution:
                    val1 = str(person[cat1])
                    val2 = str(person[cat2])
                    clue = RelationshipClue(
                        category1=cat1,
                        value1=val1,
                        category2=cat2,
                        value2=val2
                    )
                    clues.append(clue)
        
        # Add some direct position clues
        num_direct_clues = random.randint(1, min(self.num_people, len(categories_list)))
        positions_used = random.sample(range(self.num_people), num_direct_clues)
        
        for pos in positions_used:
            person = self.solution[pos]
            category = random.choice(categories_list)
            value = str(person[category])
            clue = PositionClue(
                position=pos,
                category=category,
                value=value
            )
            clues.append(clue)
        
        # Add relative position clues (left/right relationships)
        if self.num_people >= 2:
            num_relative_clues = random.randint(0, min(3, self.num_people - 1))
            
            for _ in range(num_relative_clues):
                # Pick two adjacent positions
                pos1 = random.randint(0, self.num_people - 2)
                pos2 = pos1 + 1
                
                person1 = self.solution[pos1]
                person2 = self.solution[pos2]
                
                # Pick random categories for each person
                cat1 = random.choice(categories_list)
                cat2 = random.choice(categories_list)
                
                val1 = str(person1[cat1])
                val2 = str(person2[cat2])
                
                clue = LeftOfClue(
                    category1=cat1,
                    value1=val1,
                    category2=cat2,
                    value2=val2
                )
                clues.append(clue)
        
        # Shuffle clues to make them less obvious
        random.shuffle(clues)
        
        return clues
    
    def _solve_problem_limited(self, problem: Problem, max_solutions: int = 2) -> List[List[Dict[str, Union[int, str]]]]:
        """
        Solve a CSP problem with early termination after max_solutions found.
        This is much faster when we only need to know if there are 1 or 2+ solutions.
        
        Args:
            problem: Pre-configured CSP Problem object
            max_solutions: Maximum number of solutions to find before stopping
            
        Returns:
            List of solutions (up to max_solutions)
        """
        categories_list = list(self.categories.keys())
        
        # Use getSolutionIter() for early termination
        solutions = []
        for sol in problem.getSolutionIter():
            solution: List[Dict[str, Union[int, str]]] = []
            for pos in range(self.num_people):
                person: Dict[str, Union[int, str]] = {"Position": pos}
                for category in categories_list:
                    var_name = f"pos{pos}_{category}"
                    person[category] = sol[var_name]
                solution.append(person)
            solutions.append(solution)
            
            # Early termination: stop after finding max_solutions
            if len(solutions) >= max_solutions:
                break
        
        return solutions
    
    def _solve_with_clues_limited(self, clues: List[Clue], max_solutions: int = 2) -> List[List[Dict[str, Union[int, str]]]]:
        """
        Use CSP solver to find solutions, with early termination after max_solutions found.
        This is much faster when we only need to know if there are 1 or 2+ solutions.
        
        Args:
            clues: List of structured clue objects
            max_solutions: Maximum number of solutions to find before stopping
            
        Returns:
            List of solutions (up to max_solutions)
        """
        problem = Problem()
        categories_list = list(self.categories.keys())
        
        # Create variables for each position and category
        # Variable name: "pos{position}_{category}"
        for pos in range(self.num_people):
            for category in categories_list:
                var_name = f"pos{pos}_{category}"
                problem.addVariable(var_name, self.categories[category])
        
        # Add constraint: each value in a category must be used exactly once
        for category in categories_list:
            category_vars = [f"pos{pos}_{category}" for pos in range(self.num_people)]
            problem.addConstraint(AllDifferentConstraint(), category_vars)
        
        # Add constraints from structured clues
        for clue in clues:
            self._add_clue_constraint(problem, clue)
        
        return self._solve_problem_limited(problem, max_solutions)
    
    def _add_clue_constraint(self, problem: Problem, clue: Clue):
        """
        Add constraint from a structured clue to CSP problem.
        
        Args:
            problem: CSP Problem object
            clue: Structured clue object
        """
        if isinstance(clue, RelationshipClue):
            # Constraint: if person has value1 for category1, they must have value2 for category2
            def relationship_constraint(*args):
                # args structured as: [all category1 values, all category2 values]
                # First half: values for category1 at each position
                # Second half: values for category2 at each position
                cat1_values = args[:self.num_people]
                cat2_values = args[self.num_people:]
                
                # Check each position
                for pos in range(self.num_people):
                    if cat1_values[pos] == clue.value1:
                        # Found the person with value1 for category1
                        # They must have value2 for category2
                        return cat2_values[pos] == clue.value2
                
                # If nobody has value1 for category1, constraint is satisfied
                return True
            
            # Build variable list: all cat1 variables, then all cat2 variables
            vars_for_constraint = []
            # First, add all category1 variables for each position
            for pos in range(self.num_people):
                vars_for_constraint.append(f"pos{pos}_{clue.category1}")
            # Then, add all category2 variables for each position
            for pos in range(self.num_people):
                vars_for_constraint.append(f"pos{pos}_{clue.category2}")
            
            problem.addConstraint(relationship_constraint, vars_for_constraint)
        
        elif isinstance(clue, PositionClue):
            # Constraint: person at position has value for category
            var_name = f"pos{clue.position}_{clue.category}"
            problem.addConstraint(lambda x, v=clue.value: x == v, [var_name])
        
        elif isinstance(clue, LeftOfClue):
            # Constraint: person with value1 is directly adjacent and to the left of person with value2
            # This means pos1 + 1 == pos2 (directly adjacent positions)
            def left_of_constraint(*args):
                # args structured as: [all category1 values, all category2 values]
                # First half: values for category1 at each position
                # Second half: values for category2 at each position
                cat1_values = args[:self.num_people]
                cat2_values = args[self.num_people:]
                
                # Find positions of value1 and value2
                pos1 = None
                pos2 = None
                for pos in range(self.num_people):
                    if cat1_values[pos] == clue.value1:
                        pos1 = pos
                    if cat2_values[pos] == clue.value2:
                        pos2 = pos
                
                # Both values must exist and be directly adjacent
                if pos1 is not None and pos2 is not None:
                    return pos1 + 1 == pos2  # Directly adjacent (pos1 is immediately left of pos2)
                return True
            
            # Build variable list: all cat1 variables, then all cat2 variables
            vars_for_constraint = []
            for pos in range(self.num_people):
                vars_for_constraint.append(f"pos{pos}_{clue.category1}")
            for pos in range(self.num_people):
                vars_for_constraint.append(f"pos{pos}_{clue.category2}")
            
            problem.addConstraint(left_of_constraint, vars_for_constraint)
    
    def _solutions_match(self, sol1: List[Dict[str, Union[int, str]]], sol2: Optional[List[Dict[str, Union[int, str]]]]) -> bool:
        """
        Check if two solutions are identical.
        
        Args:
            sol1: First solution
            sol2: Second solution
            
        Returns:
            True if solutions match exactly
        """
        if sol2 is None or len(sol1) != len(sol2):
            return False
        
        for p1, p2 in zip(sol1, sol2):
            if p1 != p2:
                return False
        
        return True
    
    def get_prompt(self) -> str:
        """
        Generate the puzzle prompt text to send to LLMs.
        
        Returns:
            Formatted puzzle prompt string
        """
        categories_list = [cat for cat in self.categories.keys()]
        
        prompt = f"There are {self.num_people} people attending a party. Everyone is sitting in a row. "
        prompt += f"The left most seat will be referred to as position 0, the next seat to the right will be referred to as position 1 and so on. "
        prompt += f"Each person has a {', '.join(categories_list)}.\n\n"
        
        # List possible values for each category
        for category, values in self.categories.items():
            prompt += f"The possible values for {category} are: {', '.join(values)}\n"
        
        prompt += f"\nBelow are a set of clues about each person.\n\n"
        
        # Convert structured clues to text
        clue_texts = [clue.to_text() for clue in self.clues]
        prompt += " ".join(clue_texts)
        
        prompt += f"\n\nCan you figure out what each person's {', '.join(categories_list)} are?\n\n"
        prompt += "Please write the anwser as a JSON array demarked with in <solution></solution> tags, where each element is a JSON objects. "
        prompt += "Do not include anything else in the output. For example:\n"
        prompt += "<solution>\n[\n"
        
        for i in range(self.num_people):
            prompt += "    {\n"
            prompt += f"        \"Position\": {i},\n"
            for j, category in enumerate(categories_list):
                comma = "," if j < len(categories_list) - 1 else ""
                prompt += f"        \"{category}\": \"X\"{comma}\n"
            prompt += "    }"
            if i < self.num_people - 1:
                prompt += ","
            prompt += "\n"
        
        prompt += "]\n</solution>"
        
        return prompt
    
    def get_solution_json(self) -> List[Dict]:
        """
        Get the solution as a JSON-serializable list of dicts.
        
        Returns:
            Solution in JSON format
        """
        if self.solution is None:
            return []
        return [dict(person) for person in self.solution]


def generate_puzzle(num_people: int, num_categories: int, seed: int = None) -> LogicPuzzle:
    """
    Generate a logic puzzle with specified parameters.
    
    Args:
        num_people: Number of people (1-20)
        num_categories: Number of attribute categories (1-20)
        seed: Random seed for reproducibility
        
    Returns:
        Generated LogicPuzzle instance
    """
    if seed is not None:
        random.seed(seed)

    # Generate category data
    categories = _generate_categories(num_people, num_categories)
    
    # Create and generate puzzle
    puzzle = LogicPuzzle(num_people, categories)
    success = puzzle.generate()
    
    if not success:
        print("Warning: Could not verify unique solution after maximum retries")
    
    return puzzle


def _generate_categories(num_people: int, num_categories: int) -> Dict[str, List[str]]:
    """
    Generate random category data for a puzzle.
    
    Args:
        num_people: Number of people
        num_categories: Number of categories
        
    Returns:
        Dict mapping category names to value lists
    """
    if not (1 <= num_people <= 20):
        raise ValueError("num_people must be between 1 and 20")
    if not (1 <= num_categories <= 20):
        raise ValueError("num_categories must be between 1 and 20")
    
    # Select random categories from the imported CATEGORY_NAMES
    selected_category_names = random.sample(CATEGORY_NAMES[:num_categories], num_categories)
    
    categories = {}
    for cat_name in selected_category_names:
        # Get values from pool, ensuring we have enough unique values
        pool = VALUE_POOLS[cat_name]
        categories[cat_name] = random.sample(pool, num_people)
    
    return categories


if __name__ == "__main__":
    # Test the puzzle generator
    print("Generating puzzle with CSP verification...")
    puzzle = generate_puzzle(num_people=7, num_categories=7, seed=42)
    print("\nPuzzle Prompt:")
    print(puzzle.get_prompt())
    print("\n" + "="*80 + "\n")
    print("Solution:")
    print(json.dumps(puzzle.get_solution_json(), indent=2))
    print("\n" + "="*80)
    print(f"Number of clues generated: {len(puzzle.clues)}")
    
    # Show clue type breakdown
    rel_count = sum(1 for c in puzzle.clues if isinstance(c, RelationshipClue))
    pos_count = sum(1 for c in puzzle.clues if isinstance(c, PositionClue))
    left_count = sum(1 for c in puzzle.clues if isinstance(c, LeftOfClue))
    print(f"  - Relationship clues: {rel_count}")
    print(f"  - Position clues: {pos_count}")
    print(f"  - Left-of clues: {left_count}")
