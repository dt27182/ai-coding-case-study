from typing import Any
import os
import json
from openai import OpenAI

def query_model(prompt: str, model_name: str, api_key: str = None) -> Any:
    """
    Queries the model via OpenRouter API. Returns full completion object.
    """
    if not api_key:
        api_key = os.getenv("OPEN_ROUTER_TOKEN")
        
    if not api_key:
        raise ValueError("OPEN_ROUTER_TOKEN not found in environment variables.")

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    try:
        response = client.responses.create(
            model=model_name,
            reasoning={ "effort": "medium" },
            instructions="You are a helpful assistant that solves logic grid puzzles. No puzzle is too difficult for you to solve. You will always provide a solution to the puzzle. " + \
                        "Don't write a program to solve the puzzle and don't use multiple messages. Always provide the final JSON solution in one message, " + \
                        "even if the answer is very likely to be incorrect. Do not include anything else besides the final JSON solution in the output.",
            input=f"Please solve this logic puzzle:\n\n{prompt}"
        )
        return response

    except Exception as e:
        print(f"Error querying model {model_name}: {e}")
        return None
