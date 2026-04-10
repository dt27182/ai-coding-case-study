"""
LLM Testing Module
Handles sending puzzles to LLMs via OpenRouter API and parsing responses.
"""

import os
import json
import re
import time
from typing import Dict, List, Optional, Tuple
import requests


class LLMTester:
    """Manages LLM testing via OpenRouter API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize LLM tester.
        
        Args:
            api_key: OpenRouter API key (defaults to OPEN_ROUTER_TOKEN env var)
        """
        self.api_key = api_key or os.environ.get('OPEN_ROUTER_TOKEN')
        if not self.api_key:
            raise ValueError("OpenRouter API key not provided and OPEN_ROUTER_TOKEN not set")
        
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def test_puzzle(self, puzzle_prompt: str, model: str, timeout: int = 120) -> Dict:
        """
        Send a puzzle to an LLM and get the response.
        
        Args:
            puzzle_prompt: The puzzle text to send
            model: The model identifier (e.g., "anthropic/claude-3-opus")
            timeout: Request timeout in seconds
            
        Returns:
            Dict containing:
                - success: bool
                - response: full API response dict (if successful)
                - error: error message (if failed)
                - parsed_solution: parsed solution list (if successful)
                - raw_response_text: the text response from LLM
        """
        try:
            # Prepare the request
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": puzzle_prompt
                    }
                ]
            }
            
            # Make the API call
            start_time = time.time()
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=timeout
            )
            elapsed_time = time.time() - start_time
            
            # Check for HTTP errors
            response.raise_for_status()
            
            # Parse response
            response_data = response.json()
            
            # Extract the LLM's text response
            if 'choices' in response_data and len(response_data['choices']) > 0:
                raw_response_text = response_data['choices'][0]['message']['content']
            else:
                return {
                    'success': False,
                    'error': 'No choices in response',
                    'response': response_data,
                    'elapsed_time': elapsed_time
                }
            
            # Try to parse the solution from the response
            parsed_solution = self._parse_solution(raw_response_text)
            
            return {
                'success': True,
                'response': response_data,
                'raw_response_text': raw_response_text,
                'parsed_solution': parsed_solution,
                'elapsed_time': elapsed_time
            }
            
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': f'Request timed out after {timeout} seconds'
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Request failed: {str(e)}'
            }
        except json.JSONDecodeError as e:
            return {
                'success': False,
                'error': f'Failed to parse JSON response: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }
    
    def _parse_solution(self, response_text: str) -> Optional[List[Dict]]:
        """
        Parse the LLM's solution from its response.
        
        Args:
            response_text: The raw text response from the LLM
            
        Returns:
            Parsed solution as list of dicts, or None if parsing failed
        """
        try:
            # Look for content between <solution> tags
            match = re.search(r'<solution>\s*(.*?)\s*</solution>', response_text, re.DOTALL)
            
            if not match:
                return None
            
            solution_text = match.group(1)
            
            # Parse as JSON
            solution = json.loads(solution_text)
            
            # Validate it's a list
            if not isinstance(solution, list):
                return None
            
            return solution
            
        except json.JSONDecodeError:
            return None
        except Exception:
            return None


def compare_solutions(expected: List[Dict], actual: Optional[List[Dict]]) -> Dict:
    """
    Compare expected and actual solutions.
    
    Args:
        expected: The correct solution
        actual: The LLM's solution (may be None if parsing failed)
        
    Returns:
        Dict containing:
            - correct: bool (True if solutions match exactly)
            - details: str (explanation of result)
    """
    if actual is None:
        return {
            'correct': False,
            'details': 'Failed to parse solution from LLM response'
        }
    
    # Check if lengths match
    if len(expected) != len(actual):
        return {
            'correct': False,
            'details': f'Solution length mismatch: expected {len(expected)}, got {len(actual)}'
        }
    
    # Sort both solutions by Position to ensure consistent comparison
    try:
        expected_sorted = sorted(expected, key=lambda x: x.get('Position', -1))
        actual_sorted = sorted(actual, key=lambda x: x.get('Position', -1))
    except Exception as e:
        return {
            'correct': False,
            'details': f'Error sorting solutions: {str(e)}'
        }
    
    # Compare each person
    for i, (exp_person, act_person) in enumerate(zip(expected_sorted, actual_sorted)):
        # Check if all keys match
        exp_keys = set(exp_person.keys())
        act_keys = set(act_person.keys())
        
        if exp_keys != act_keys:
            missing = exp_keys - act_keys
            extra = act_keys - exp_keys
            details = f"Position {i}: Key mismatch"
            if missing:
                details += f", missing keys: {missing}"
            if extra:
                details += f", extra keys: {extra}"
            return {
                'correct': False,
                'details': details
            }
        
        # Check if all values match
        for key in exp_keys:
            if exp_person[key] != act_person[key]:
                return {
                    'correct': False,
                    'details': f"Position {i}: {key} mismatch (expected: {exp_person[key]}, got: {act_person[key]})"
                }
    
    return {
        'correct': True,
        'details': 'Solution matches exactly'
    }


if __name__ == "__main__":
    # Test the LLM tester
    tester = LLMTester()
    
    # Simple test puzzle
    test_prompt = """There are 2 people attending a party. Everyone is sitting in a row. The left most seat will be referred to as position 0, the next seat to the right will be referred to as position 1 and so on. Each person has a name, color.

The possible values for name are: Alice, Bob
The possible values for color are: Red, Blue

Below are a set of clues about each person.

The person sitting at position 0 has Alice as their name. The person who has Alice as their name also has Red as their color. The person sitting at position 1 has Bob as their name. The person who has Bob as their name also has Blue as their color.

Can you figure out what each person's name, color are?

Please write the anwser as a JSON array demarked with in <solution></solution> tags, where each element is a JSON objects. Do not include anything else in the output. For example:
<solution>
[
    {
        "Position": 0,
        "name": "X",
        "color": "X"
    },
    {
        "Position": 1,
        "name": "X",
        "color": "X"
    }
]
</solution>"""
    
    print("Testing LLM with simple puzzle...")
    result = tester.test_puzzle(test_prompt, "anthropic/claude-3-haiku")
    print(json.dumps(result, indent=2))
