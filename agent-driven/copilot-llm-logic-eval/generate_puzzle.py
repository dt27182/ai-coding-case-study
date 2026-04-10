import random
from solve_puzzle import create_solver_with_clues
from attribute_pool import ATTRIBUTE_POOL


class ZebraPuzzleGenerator:
    CLUE_TYPES = ['same_person', 'left_of', 'position']
    
    def __init__(self, num_people, num_attributes_per_person):
        self.num_people = num_people
        self.num_attributes_per_person = num_attributes_per_person
        self.attributes = {}
        self.clues = []
        self.target_solution = {}
        
    def generate_puzzle(self):
        self._generate_attributes()
        self._generate_target_solution()
        self._generate_clues_from_solution()
        return {
            'num_people': self.num_people,
            'attributes': self.attributes,
            'clues': self.clues,
            'text': self._format_puzzle_text()
        }
    
    def _generate_attributes(self):
        self.attributes['Name'] = random.sample(ATTRIBUTE_POOL['Name'], min(self.num_people, len(ATTRIBUTE_POOL['Name'])))
        
        available_attributes = [attr for attr in ATTRIBUTE_POOL.keys() if attr != 'Name']
        random.shuffle(available_attributes)
        
        num_additional_attributes = self.num_attributes_per_person - 1
        selected_attributes = available_attributes[:num_additional_attributes]
        
        for attr_name in selected_attributes:
            all_values = ATTRIBUTE_POOL[attr_name]
            selected_values = random.sample(all_values, min(self.num_people, len(all_values)))
            self.attributes[attr_name] = selected_values
    
    def _generate_target_solution(self):
        for attr_name, values in self.attributes.items():
            shuffled_values = values.copy()
            random.shuffle(shuffled_values)
            for person_id in range(self.num_people):
                person_key = f"person_{person_id}"
                if person_key not in self.target_solution:
                    self.target_solution[person_key] = {}
                self.target_solution[person_key][attr_name] = shuffled_values[person_id]
    
    def _generate_clues_from_solution(self):
        all_possible_clues = self._generate_all_possible_clues()
        random.shuffle(all_possible_clues)
        
        num_attributes = len(self.attributes)
        
        difficulty = max(self.num_people, num_attributes) ** 2
        if difficulty <= 100:
            num_initial_clues = min(int(self.num_people * num_attributes * 1.4), len(all_possible_clues))
        elif difficulty < 225:
            num_initial_clues = min(int(difficulty * 2), len(all_possible_clues))
        elif difficulty < 289:
            num_initial_clues = min(int(difficulty * 2.3), len(all_possible_clues))
        else:
            num_initial_clues = min(int(difficulty * 3.1), len(all_possible_clues))
        
        num_clues_per_iteration = max(1, random.randint(
            int(self.num_people * num_attributes * 0.06) - 1,
            int(self.num_people * num_attributes * 0.06) + 1
        ))
        
        print(f"  Starting with initial batch of {num_initial_clues} clues (difficulty={difficulty})...")
        self.clues = all_possible_clues[:num_initial_clues]
        remaining_clues = all_possible_clues[num_initial_clues:]
        
        solver = create_solver_with_clues(self.num_people, self.attributes, self.clues)
        if solver.has_unique_solution():
            print(f"  ✓ Unique solution found with {len(self.clues)} clues")
            return
        
        print(f"  Adding clues in batches of {num_clues_per_iteration}...")
        batch_count = 0
        for i in range(0, len(remaining_clues), num_clues_per_iteration):
            batch = remaining_clues[i:i+num_clues_per_iteration]
            self.clues.extend(batch)
            batch_count += 1
            
            solver = create_solver_with_clues(self.num_people, self.attributes, self.clues)
            
            if solver.has_unique_solution():
                print(f"  ✓ Unique solution found after {batch_count} batches ({len(self.clues)} total clues)")
                return
        
        raise Exception(f"Failed to generate solvable puzzle after trying all possible clues")
    
    def _generate_all_possible_clues(self):
        clues = []
        
        clues.extend(self._generate_all_position_clues())
        clues.extend(self._generate_all_same_person_clues())
        clues.extend(self._generate_all_left_of_clues())
        
        return clues
    
    def _generate_all_position_clues(self):
        clues = []
        for attr_name in self.attributes.keys():
            for person_id in range(self.num_people):
                person_key = f"person_{person_id}"
                val = self.target_solution[person_key][attr_name]
                clues.append({
                    'type': 'position',
                    'attr': attr_name,
                    'val': val,
                    'position': person_id
                })
        return clues
    
    def _generate_all_same_person_clues(self):
        clues = []
        attr_list = list(self.attributes.keys())
        
        for i, attr1 in enumerate(attr_list):
            for attr2 in attr_list[i+1:]:
                for person_id in range(self.num_people):
                    person_key = f"person_{person_id}"
                    val1 = self.target_solution[person_key][attr1]
                    val2 = self.target_solution[person_key][attr2]
                    clues.append({
                        'type': 'same_person',
                        'attr1': attr1,
                        'val1': val1,
                        'attr2': attr2,
                        'val2': val2
                    })
        return clues
    
    def _generate_all_left_of_clues(self):
        clues = []
        attr_list = list(self.attributes.keys())
        
        for attr1 in attr_list:
            for attr2 in attr_list:
                for left_person_id in range(self.num_people - 1):
                    right_person_id = left_person_id + 1
                    
                    left_person_key = f"person_{left_person_id}"
                    right_person_key = f"person_{right_person_id}"
                    val1 = self.target_solution[left_person_key][attr1]
                    val2 = self.target_solution[right_person_key][attr2]
                    
                    clues.append({
                        'type': 'left_of',
                        'attr1': attr1,
                        'val1': val1,
                        'attr2': attr2,
                        'val2': val2
                    })
        return clues
    
    def _format_puzzle_text(self):
        lines = []
        lines.append(f"There are {self.num_people} people attending a party. Everyone is sitting in a row. The left most seat will be referred to as position 0, the next seat to the right will be referred to as position 1 and so on. Each person has {', '.join(self.attributes.keys())}.")
        lines.append("")
        for attr_name, values in self.attributes.items():
            lines.append(f"The possible values for {attr_name.lower()} are: {', '.join(values)}")
        lines.append("")
        lines.append("Below are a set of clues about each person.")
        lines.append("")
        for clue in self.clues:
            lines.append(self._format_clue(clue))
        lines.append("")
        attribute_list = ', '.join(attr_name.lower() for attr_name in self.attributes.keys())
        lines.append(f"Can you figure out what each person's {attribute_list} are?")
        return "\n".join(lines)
    
    def _format_clue(self, clue):
        clue_type = clue['type']
        
        if clue_type == 'same_person':
            return f"The person who has {clue['val1']} as their {clue['attr1'].lower()} also has {clue['val2']} as their {clue['attr2'].lower()}."
        elif clue_type == 'left_of':
            return f"The person who has {clue['val1']} as their {clue['attr1'].lower()} is sitting to the left of the person who has {clue['val2']} as their {clue['attr2'].lower()}."
        elif clue_type == 'position':
            return f"The person sitting at position {clue['position']} has {clue['val']} as their {clue['attr'].lower()}."


def generate_puzzle(num_people, num_attributes):
    generator = ZebraPuzzleGenerator(num_people, num_attributes)
    return generator.generate_puzzle()


if __name__ == '__main__':
    import argparse
    import json
    from solve_puzzle import create_solver_with_clues
    
    parser = argparse.ArgumentParser(description="Generate a Zebra logic puzzle")
    parser.add_argument('-p', '--num-people', type=int, default=3, help='Number of people in the puzzle (default: 3)')
    parser.add_argument('-a', '--num-attributes', type=int, default=3, help='Number of attributes per person (default: 3)')
    args = parser.parse_args()
    
    print("Testing puzzle generator...")
    print("=" * 80)
    
    print(f"\nGenerating puzzle with {args.num_people} people and {args.num_attributes} attributes...\n")
    
    puzzle = generate_puzzle(args.num_people, args.num_attributes)
    
    print(puzzle['text'])
    print("\n" + "=" * 80)
    
