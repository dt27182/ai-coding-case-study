import random
from typing import List, Dict, Any, Tuple
import constraint
from src.data import TIERS

class LogicPuzzle:
    def __init__(self, num_people: int, num_attributes: int):
        self.num_people = num_people
        self.num_attributes = num_attributes
        
        # Select categories for this puzzle
        # We always use "Order" (implied position 0..N-1) as the anchor, so we need num_attributes lists of values.
        # Actually, usually "Name" is a primary attribute too.
        # Let's say we have N positions.
        # attributes keys: "Name", "Color", etc. values: list of strings
        available_categories = list(TIERS.keys())
        if "Name" in available_categories:
            available_categories.remove("Name")
        
        selected_cats = ["Name"] + random.sample(available_categories, num_attributes - 1)
        self.categories: Dict[str, List[str]] = {} # Category Name -> List of Values
        
        for cat in selected_cats:
            self.categories[cat] = random.sample(TIERS[cat], num_people)
            
        self.ground_truth: List[Dict[str, str]] = [] # List of people (dicts)
        self.clues: List[str] = []
        self.solution_constraints = [] # To be used for solver verification
        
    def generate_ground_truth(self):
        # Assign attributes to positions 0..N-1
        # For each category, shuffle the values and assign to positions.
        # Structure: self.ground_truth = [{'Position': 0, 'Name': 'Bob', ...}, ...]
        
        temp_data = {cat: list(vals) for cat, vals in self.categories.items()}
        for cat in temp_data:
            random.shuffle(temp_data[cat])
            
        self.ground_truth = []
        for i in range(self.num_people):
            person = {"Position": i}
            for cat in self.categories:
                person[cat] = temp_data[cat][i]
            self.ground_truth.append(person)
            
    def _generate_candidate_clues(self):
        # Generate a pool of potential clues based on ground truth
        candidates = []
        
        # 1. Direct Assignment (Person at pos X is Y, Person with Name X has Pet Y)
        # 2. Relative Position (X is left of Y, X is next to Y)
        
        # Generate all valid "Link" clues (Attribute A Val 1 <-> Attribute B Val 2)
        for i in range(self.num_people):
            p = self.ground_truth[i]
            # Gather all (Category, Value) pairs for this person
            attrs = [(k, v) for k, v in p.items() if k != "Position"]
            # Add Position explicitly as (Position, i)
            attrs.append(("Position", i))
            
            # Pairwise combinations
            for (cat1, val1) in attrs:
                for (cat2, val2) in attrs:
                    if cat1 == cat2: continue
                    
                    # LINK CLUE: "The [Val1] [Cat1] is the [Val2] [Cat2]" 
                    # specialized phrasing based on categories
                    
                    # We store the semantic meaning to pass to the solver checker
                    # (Type, Cat1, Val1, Cat2, Val2)
                    candidates.append({
                        "type": "link",
                        "c1": cat1, "v1": val1,
                        "c2": cat2, "v2": val2,
                        "text": self.format_link_clue(cat1, val1, cat2, val2)
                    })
        
        # Generate spatial clues
        for i in range(self.num_people - 1):
            p1 = self.ground_truth[i]
            p2 = self.ground_truth[i+1]
            
            # Adjacent Pair: p1 is at pos i, p2 is at pos i+1
            # Relation: p1 is immediately left of p2
            # Relation: p2 is immediately right of p1
            
            # Pick attributes
            c1 = random.choice(list(self.categories.keys()))
            c2 = random.choice(list(self.categories.keys()))
            v1 = p1[c1]
            v2 = p2[c2]
            
            # Randomly decide between stating "Left" or "Right"
            if random.random() < 0.5:
                # "The [v1] [c1] is sitting to the left of [v2] [c2]"
                candidates.append({
                    "type": "immediate_left",
                    "c1": c1, "v1": v1,
                    "c2": c2, "v2": v2,
                    "text": f"The person who has {v1} as their {c1.lower()} is sitting to the left of the person who has {v2} as their {c2.lower()}."
                })
            else:
                # "The [v2] [c2] is sitting to the right of [v1] [c1]"
                # Note: v2 (right person) is right of v1 (left person)
                candidates.append({
                    "type": "immediate_right",
                    "c1": c2, "v1": v2,
                    "c2": c1, "v2": v1,
                    "text": f"The person who has {v2} as their {c2.lower()} is sitting to the right of the person who has {v1} as their {c1.lower()}."
                })
        return candidates

    def generate_clues(self):
        candidates = self._generate_candidate_clues()
        
        
        random.shuffle(candidates)
        
        # Greedy Selection Strategy:
        # Start with empty constraints.
        # Add clues 1 by 1. Check solution count.
        # Stop when count == 1.
        
        self.clues = []
        active_constraints = []
        
        # Batch size for checking uniqueness
        # Checking every single clue is too slow for large puzzles.
        # We assume clues generated from ground truth are valid.
        batch_size = 1
        if self.num_people >= 5:
            batch_size = 3
        if self.num_people >= 10:
            batch_size = 5
        if self.num_people >= 15:
            # For very large puzzles, initially add many clues before checking.
            # But here we just set a larger stride.
            batch_size = 10
        
        for i, cand in enumerate(candidates):
            # Optimization: Try to prioritize clues that link unconnected components? 
            # For now, just random order.
            
            # Add the clue unconditionally first
            active_constraints.append(cand)
            self.clues.append(cand["text"])
            
            # Heuristic: Don't check at all until we have a critical mass of clues.
            # Using reference implementation logic for aggressive optimization.
            difficulty = max(self.num_people, self.num_attributes) ** 2
            if difficulty <= 100:
                safe_start_threshold = min(int(self.num_people * self.num_attributes * 1.4), len(candidates))
            elif difficulty < 225:
                safe_start_threshold = min(int(difficulty * 2), len(candidates))
            elif difficulty < 289:
                safe_start_threshold = min(int(difficulty * 2.3), len(candidates))
            else:
                safe_start_threshold = min(int(difficulty * 3.1), len(candidates))

            if len(active_constraints) < safe_start_threshold:
                continue

            # Check only every batch_size or if it's the last candidate
            # This significantly reduces overhead of calling the solver repeatedly.
            if (i + 1) % batch_size == 0 or (i + 1) == len(candidates):
                sol_count = self.solve(active_constraints, max_solutions=2)
                if sol_count == 1:
                    break
                
        self.constraints_data = active_constraints
        # If we run out of clues and still > 1 solution, the puzzle is ambiguous (failed to generate)
        # But we generated clues from ground truth, so it should be consistent.
        # If we fail to narrow it down, we might need more clues (or specific types we missed).
        
    def format_link_clue(self, c1, v1, c2, v2):
        # "The [Val1] [Cat1] is the [Val2] [Cat2]"
        # "The person with [Val1] [Cat1]..."
        
        # Position special handling
        if c1 == "Position":
            s1 = f"The person sitting at position {v1}"
        else:
            s1 = f"The person who has {v1} as their {c1.lower()}"
            
        if c2 == "Position":
            s2 = f"is sitting at position {v2}"
        else:
            s2 = f"also has {v2} as their {c2.lower()}"
            
        return f"{s1} {s2}."

    def solve(self, constraints_list, max_solutions=0):
        # Uses python-constraint to solve or count solutions
        problem = constraint.Problem()
        
        # Variables: (Category, Value) -> Position (0..N-1)
        # We assume Position 0..N-1 exists.
        # Unary attributes are implicit.
        
        # Define variables
        # For every Value in every Category, where is it?
        variables = []
        for cat, values in self.categories.items():
            for val in values:
                var_name = f"{cat}:{val}" # "Color:Red"
                problem.addVariable(var_name, range(self.num_people))
                variables.append(var_name)
        
        # Generic Constraints:
        # 1. AllDifferent within a Category (Red and Blue cannot be at same pos)
        for cat, values in self.categories.items():
            cat_vars = [f"{cat}:{val}" for val in values]
            problem.addConstraint(constraint.AllDifferentConstraint(), cat_vars)
            
        # 2. Apply Specific Constraints
        for c in constraints_list:
            t = c["type"]
            # Variable names
            # If c1 is Position, we are constraining the value of c2
            # If c2 is Position, we are constraining the value of c1
            
            if t == "link":
                # c1:v1 == c2:v2 (share same position)
                
                # Handle Position logic
                if c["c1"] == "Position":
                    # "Person at Pos X has Val2" -> Var(c2:v2) == X
                    problem.addConstraint(lambda x, v=c["v1"]: x == v, [f"{c['c2']}:{c['v2']}"])
                elif c["c2"] == "Position":
                    problem.addConstraint(lambda x, v=c["v2"]: x == v, [f"{c['c1']}:{c['v1']}"])
                else:
                    problem.addConstraint(lambda x, y: x == y, [f"{c['c1']}:{c['v1']}", f"{c['c2']}:{c['v2']}"])
                    
            elif t == "immediate_left":
                # p1 left of p2 -> Pos(p1) + 1 == Pos(p2)
                # Not possible if c1/c2 is Position (handled in clues gen to avoid this ambiguity for now)
                
                problem.addConstraint(
                    lambda x, y: x + 1 == y, 
                    [f"{c['c1']}:{c['v1']}", f"{c['c2']}:{c['v2']}"]
                )

            elif t == "immediate_right":
                # p1 right of p2 -> Pos(p1) - 1 == Pos(p2)
                
                problem.addConstraint(
                    lambda x, y: x - 1 == y, 
                    [f"{c['c1']}:{c['v1']}", f"{c['c2']}:{c['v2']}"]
                )
                


        # Get solutions
        if max_solutions > 0:
            solutions = []
            # python-constraint doesn't have max_solutions arg in getSolutions, but has getSolutionIter
            iter_sol = problem.getSolutionIter()
            try:
                for _ in range(max_solutions + 1):
                    solutions.append(next(iter_sol))
            except StopIteration:
                pass
            return len(solutions)
        else:
             return len(problem.getSolutions())

    def render_prompt(self):
        # Text description
        lines = []
        lines.append(f"There are {self.num_people} people attending a party. Everyone is sitting in a row. The left most seat will be referred to as position 0, the next seat to the right will be referred to as position 1 and so on.")
        lines.append("Each person has a " + ", ".join([c.lower() for c in self.categories.keys()]) + ".")
        lines.append("")
        
        for cat, vals in self.categories.items():
            lines.append(f"The possible values for {cat.lower()} are: {', '.join(vals)}")
        
        lines.append("")
        lines.append("Below are a set of clues about each person.")
        lines.append("")
        for clue in self.clues:
            lines.append(clue)
            
        lines.append("")
        lines.append("Can you figure out what each person's " + ", ".join([c.lower() for c in self.categories.keys()]) + " are?")
        lines.append("Please output the answer as a JSON object, specifically a list of objects where each object represents a person at a position.")
        
        # specific example generation
        example_data = []
        for i in range(self.num_people):
            person_ex = {"Position": i}
            for cat in self.categories:
                person_ex[cat] = "X"
            example_data.append(person_ex)
            
        import json
        lines.append("Example format:")
        lines.append(json.dumps(example_data, indent=2))
        
        return "\n".join(lines)

if __name__ == "__main__":
    # Test
    p = LogicPuzzle(3, 3)
    p.generate_ground_truth()
    print("Ground Truth:", p.ground_truth)
    p.generate_clues()
    print("Clues:", len(p.clues))
    for c in p.clues:
        print("-", c)
    print("\nPrompt:\n", p.render_prompt())
