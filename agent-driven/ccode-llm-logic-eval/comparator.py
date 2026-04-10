"""Solution comparison and parsing logic."""

import json
import re
from typing import Dict, List, Any, Tuple, Optional


def parse_solution(llm_response: str) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
    """
    Parse LLM response to extract solution from <solution> tags.

    Args:
        llm_response: Raw text response from LLM

    Returns:
        Tuple of (parsed_solution, error_message)
        If parsing succeeds: (solution_list, None)
        If parsing fails: (None, error_message)
    """
    try:
        # Extract content between <solution> tags
        match = re.search(r'<solution>(.*?)</solution>', llm_response, re.DOTALL)

        if not match:
            return None, "No <solution> tags found in response"

        solution_text = match.group(1).strip()

        # Parse JSON
        try:
            solution = json.loads(solution_text)
        except json.JSONDecodeError as e:
            return None, f"JSON parsing error: {str(e)}"

        # Validate structure
        if not isinstance(solution, list):
            return None, "Solution is not a JSON array"

        if len(solution) == 0:
            return None, "Solution array is empty"

        # Validate each element is a dict with Position key
        for i, person in enumerate(solution):
            if not isinstance(person, dict):
                return None, f"Element {i} is not a JSON object"
            if "Position" not in person:
                return None, f"Element {i} missing 'Position' key"

        return solution, None

    except Exception as e:
        return None, f"Unexpected error during parsing: {str(e)}"


def compare_solutions(
    actual_solution: List[Dict[str, Any]],
    llm_solution: List[Dict[str, Any]]
) -> Tuple[bool, List[str]]:
    """
    Compare actual solution with LLM solution.

    Args:
        actual_solution: Ground truth solution
        llm_solution: Solution parsed from LLM response

    Returns:
        Tuple of (exact_match, differences)
        exact_match: True if solutions match completely
        differences: List of difference descriptions
    """
    differences = []

    # Check if lengths match
    if len(actual_solution) != len(llm_solution):
        differences.append(
            f"Different number of people: expected {len(actual_solution)}, "
            f"got {len(llm_solution)}"
        )
        return False, differences

    # Sort both solutions by Position for comparison
    actual_sorted = sorted(actual_solution, key=lambda x: x["Position"])
    llm_sorted = sorted(llm_solution, key=lambda x: x["Position"])

    # Compare position by position
    for actual_person, llm_person in zip(actual_sorted, llm_sorted):
        pos = actual_person["Position"]

        # Check if positions match
        if llm_person["Position"] != pos:
            differences.append(
                f"Position mismatch at index: expected {pos}, got {llm_person['Position']}"
            )
            continue

        # Get all attributes from actual solution
        actual_attrs = {k: v for k, v in actual_person.items() if k != "Position"}
        llm_attrs = {k: v for k, v in llm_person.items() if k != "Position"}

        # Check for missing attributes
        for attr in actual_attrs:
            if attr not in llm_attrs:
                differences.append(
                    f"Position {pos}: missing attribute '{attr}'"
                )
                continue

            # Check if values match
            if actual_attrs[attr] != llm_attrs[attr]:
                differences.append(
                    f"Position {pos}, {attr}: expected '{actual_attrs[attr]}', "
                    f"got '{llm_attrs[attr]}'"
                )

        # Check for extra attributes
        for attr in llm_attrs:
            if attr not in actual_attrs:
                differences.append(
                    f"Position {pos}: unexpected attribute '{attr}'"
                )

    exact_match = len(differences) == 0
    return exact_match, differences


def evaluate_response(
    llm_response: str,
    actual_solution: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Parse and evaluate an LLM response.

    Args:
        llm_response: Raw text response from LLM
        actual_solution: Ground truth solution

    Returns:
        Dictionary containing parsing results and evaluation
    """
    # Parse the response
    parsed_solution, parsing_error = parse_solution(llm_response)

    result = {
        "raw_text": llm_response,
        "parsed_solution": parsed_solution,
        "parsing_error": parsing_error
    }

    # If parsing failed, return early
    if parsing_error:
        return result

    # Compare solutions
    exact_match, differences = compare_solutions(actual_solution, parsed_solution)

    result["evaluation"] = {
        "exact_match": exact_match,
        "differences": differences
    }

    return result
