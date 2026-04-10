import json
import re
from typing import List, Dict, Any, Tuple

def extract_json(text: str) -> str:
    """
    Extracts JSON from text, handling markdown code blocks.
    """
    # Try to find JSON inside ```json ... ``` or ``` ... ```
    match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if match:
        return match.group(1)
    
    # If no blocks, assumes the whole text might be JSON
    return text.strip()

def normalize_key(k: str) -> str:
    return k.lower().strip()

def normalize_val(v: str) -> str:
    return str(v).lower().strip()

def verify_json(response_text: str, ground_truth: List[Dict[str, str]]) -> Tuple[bool, str, Any]:
    """
    Verifies if the response matches the ground truth.
    Returns: (is_correct, status_message, parsed_json)
    """
    json_text = extract_json(response_text)
    
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError:
        return False, "JSON Parse Error", None
        
    if not isinstance(data, list):
        return False, "Root element is not a list", data
        
    if len(data) != len(ground_truth):
        return False, f"Length mismatch: Expected {len(ground_truth)}, got {len(data)}", data
        
    # Sort both lists by Position to align them
    try:
        data_sorted = sorted(data, key=lambda x: int(x.get("Position", -1)))
        truth_sorted = sorted(ground_truth, key=lambda x: int(x.get("Position", -1)))
    except (ValueError, TypeError):
        return False, "Invalid 'Position' keys in response", data
        
    for i, (pred, true) in enumerate(zip(data_sorted, truth_sorted)):
        # Check every key in expected truth
        for key, true_val in true.items():
            # Key might be case insensitive in prediction?
            # Let's try direct match first, then lower case match
            
            # Simple approach: Check if key exists in pred
            # We normalized keys in generator ("Name", "Color") so let's expect title case or similar.
            # But user prompt uses lower case in "possible values for name...". 
            # The Example Output used Title Case keys "Position", "Name".
            
            # Let's be lenient on casing for keys and values
            
            pred_val = None
            found_key = False
            for k, v in pred.items():
                if normalize_key(k) == normalize_key(key):
                    pred_val = v
                    found_key = True
                    break
            
            if not found_key:
                return False, f"Missing key '{key}' for person at Position {i}", data
                
            if normalize_val(pred_val) != normalize_val(true_val):
                return False, f"Mismatch at Position {i}, Attribute '{key}': Expected '{true_val}', Got '{pred_val}'", data
                
    return True, "Correct", data
