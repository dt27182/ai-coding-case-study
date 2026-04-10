"""OpenRouter API client for querying LLMs."""

import json
import requests
import time
import logging
from typing import Dict, Any, Optional, Tuple


class OpenRouterClient:
    """Client for interacting with OpenRouter API using Responses API."""

    BASE_URL = "https://openrouter.ai/api/v1/responses"

    def __init__(self, api_key: str, logger: Optional[logging.Logger] = None):
        """Initialize the OpenRouter client."""
        self.api_key = api_key
        self.logger = logger or logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://github.com/dtang/ccode-llm-logic-eval",
            "X-Title": "Logic Puzzle LLM Evaluation"
        })

    def query_model(
        self,
        model: str,
        prompt: str,
        timeout: int = 120
    ) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Query a model via OpenRouter Responses API.

        Args:
            model: Model identifier (e.g., "openai/gpt-4")
            prompt: The prompt to send
            timeout: Request timeout in seconds

        Returns:
            Tuple of (response_text, api_info) where api_info contains
            response_time_ms and tokens_used
        """
        payload = {
            "model": model,
            "input": prompt,
            "reasoning": {"effort": "medium"},
            "instructions": (
                "You are a helpful assistant that solves logic grid puzzles. "
                "No puzzle is too difficult for you to solve. You will always provide a solution to the puzzle. "
                "Don't write a program to solve the puzzle and don't use multiple messages. "
                "Always provide the final JSON solution in one message, "
                "even if the answer is very likely to be incorrect. "
                "Do not include anything else besides the final JSON solution in the output."
            )
        }

        try:
            start_time = time.time()
            response = self.session.post(
                self.BASE_URL,
                json=payload,
                timeout=timeout
            )
            response_time_ms = int((time.time() - start_time) * 1000)

            response.raise_for_status()

            data = response.json()
            self.logger.debug("API Response:\n" + json.dumps(data, indent=2))

            if data.get("error"):
                self.logger.error(f"API error: {data['error']}")
                return None, {
                    "response_time_ms": response_time_ms,
                    "tokens_used": None,
                    "error": data["error"]
                }

            if "output" not in data or len(data["output"]) == 0:
                self.logger.error("No output in response")
                return None, {
                    "response_time_ms": response_time_ms,
                    "tokens_used": None,
                    "error": "No output in response"
                }

            # Find the message output item (skip reasoning items)
            response_text = None
            for output_item in data["output"]:
                if output_item.get("type") == "message":
                    # Content is an array of content blocks
                    content = output_item.get("content", [])
                    if content and isinstance(content, list):
                        for block in content:
                            if block.get("type") == "output_text":
                                response_text = block.get("text", "")
                                break
                    break

            if response_text is None:
                # Fallback: try the old format
                output_item = data["output"][0]
                if "content" in output_item:
                    response_text = output_item["content"]
                elif "text" in output_item:
                    response_text = output_item["text"]
                else:
                    response_text = str(output_item)
                    self.logger.warning(f"Unexpected output format, using: {response_text[:100]}")

            tokens_used = None
            if "usage" in data:
                tokens_used = data["usage"].get("total_tokens")

            api_info = {
                "response_time_ms": response_time_ms,
                "tokens_used": tokens_used
            }

            self.logger.info(
                f"Received response from {model} ({response_time_ms}ms, "
                f"{tokens_used or 'unknown'} tokens)"
            )

            return response_text, api_info

        except requests.exceptions.Timeout:
            self.logger.error("Request timeout")
            return None, {
                "response_time_ms": timeout * 1000,
                "tokens_used": None,
                "error": "Request timeout"
            }

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request error: {e}")
            return None, {
                "response_time_ms": 0,
                "tokens_used": None,
                "error": str(e)
            }


def format_prompt(puzzle: Dict[str, Any]) -> str:
    """Format a puzzle into a prompt for the LLM."""
    num_people = puzzle["num_people"]
    attributes = puzzle["attributes"]
    clues = puzzle["clues"]

    # Get attribute names (excluding Position)
    attr_names = [attr for attr in attributes.keys()]

    # Format attribute list for natural language
    if len(attr_names) == 1:
        attr_list = attr_names[0]
    elif len(attr_names) == 2:
        attr_list = f"{attr_names[0]} and {attr_names[1]}"
    else:
        attr_list = ", ".join(attr_names[:-1]) + f", and {attr_names[-1]}"

    # Build prompt
    prompt_parts = [
        f"There are {num_people} people attending a party. Everyone is sitting in a row. "
        f"The left most seat will be referred to as position 0, the next seat to the right "
        f"will be referred to as position 1 and so on. Each person has a {attr_list}.",
        ""
    ]

    # Add possible values for each attribute
    for attr in attr_names:
        values = ", ".join(attributes[attr])
        prompt_parts.append(f"The possible values for {attr} are: {values}")

    prompt_parts.append("")
    prompt_parts.append("Below are a set of clues about each person.")
    prompt_parts.append("")

    # Add clues
    for clue in clues:
        prompt_parts.append(clue)

    prompt_parts.append("")
    prompt_parts.append(f"Can you figure out what each person's {attr_list} are?")
    prompt_parts.append("")
    prompt_parts.append(
        "Please write the answer as a JSON array demarked within <solution></solution> tags, "
        "where each element is a JSON object. Do not include anything else in the output. "
        "For example:"
    )
    prompt_parts.append("<solution>")

    # Build example format
    example = "[\n"
    for i in range(num_people):
        example += f'    {{"Position": {i}'
        for attr in attr_names:
            example += f', "{attr}": "X"'
        example += "}"
        if i < num_people - 1:
            example += ","
        example += "\n"
    example += "]"

    prompt_parts.append(example)
    prompt_parts.append("</solution>")

    return "\n".join(prompt_parts)
