import json


def evaluate_solution(llm_solution, ground_truth):
    if llm_solution is None:
        return {
            'correct': False,
            'reason': 'Failed to parse LLM solution'
        }
    
    if not isinstance(llm_solution, dict) or not isinstance(ground_truth, dict):
        return {
            'correct': False,
            'reason': 'Invalid solution format'
        }
    
    if set(llm_solution.keys()) != set(ground_truth.keys()):
        return {
            'correct': False,
            'reason': 'Mismatched person keys'
        }
    
    for person_key in ground_truth.keys():
        if person_key not in llm_solution:
            return {
                'correct': False,
                'reason': f'Missing person: {person_key}'
            }
        
        llm_attrs = llm_solution[person_key]
        truth_attrs = ground_truth[person_key]
        
        if not isinstance(llm_attrs, dict) or not isinstance(truth_attrs, dict):
            return {
                'correct': False,
                'reason': f'Invalid attributes for {person_key}'
            }
        
        if set(llm_attrs.keys()) != set(truth_attrs.keys()):
            return {
                'correct': False,
                'reason': f'Mismatched attributes for {person_key}'
            }
        
        for attr_key in truth_attrs.keys():
            if llm_attrs[attr_key] != truth_attrs[attr_key]:
                return {
                    'correct': False,
                    'reason': f'Incorrect value for {person_key}.{attr_key}: expected {truth_attrs[attr_key]}, got {llm_attrs[attr_key]}'
                }
    
    return {
        'correct': True,
        'reason': 'Exact match'
    }


def calculate_accuracy(evaluation_results):
    if not evaluation_results:
        return 0.0
    
    correct_count = sum(1 for result in evaluation_results if result['evaluation']['correct'])
    total_count = len(evaluation_results)
    
    return correct_count / total_count if total_count > 0 else 0.0
