import re
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI


class OpenRouterClient:
    def __init__(self, api_key):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
    
    def create_prompt(self, puzzle_text):
        # Extract attribute names from puzzle text to build example JSON
        # The puzzle_text contains lines like "Each person has name, city, dessert, movie genre."
        import re
        match = re.search(r'Each person has (.+?)\.', puzzle_text)
        if match:
            attrs_str = match.group(1)
            attributes = [attr.strip() for attr in attrs_str.split(',')]
        else:
            attributes = ['attribute1', 'attribute2']
        
        # Extract number of people
        people_match = re.search(r'There are (\d+) people', puzzle_text)
        num_people = int(people_match.group(1)) if people_match else 2
        
        # Build example JSON structure in old object format
        example_obj = {}
        for i in range(num_people):
            person_key = f"person_{i}"
            person_attrs = {}
            for attr in attributes:
                person_attrs[attr] = "X"
            example_obj[person_key] = person_attrs
        
        example_json = json.dumps(example_obj, indent=2)
        
        prompt = f"""{puzzle_text}

Please write the answer as a JSON object demarked within <solution></solution> tags. Do not include anything else in the output. For example:
<solution>
{example_json}
</solution>"""
        return prompt
    
    def query_model(self, model_name, puzzle_text):
        prompt = self.create_prompt(puzzle_text)
        
        start_time = time.time()
        
        response = self.client.responses.create(
            model=model_name,
            reasoning={"effort": "medium"},
            instructions="You are a helpful assistant that solves logic grid puzzles. No puzzle is too difficult for you to solve. You will always provide a solution to the puzzle. " + \
                "Don't write a program to solve the puzzle and don't use multiple messages. Always provide the final JSON solution in one message, " + \
                "even if the answer is very likely to be incorrect. Do not include anything else besides the final JSON solution in the output.",
            input=prompt,
        )
        full_response = response.model_dump()
        response_text = response.output_text
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        return {
            'model': model_name,
            'prompt': prompt,
            'response': response_text,
            'full_response': full_response,
            'error': None,
            'elapsed_time': elapsed_time,
            'timestamp': time.time()
        }
    

def extract_solution_json(response_text):
    if not response_text:
        return None
    
    pattern = r'<solution>(.*?)</solution>'
    match = re.search(pattern, response_text, re.DOTALL)
    
    if not match:
        return None
    
    json_text = match.group(1).strip()
    
    solution = json.loads(json_text)
    return solution
