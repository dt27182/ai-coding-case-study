"""Utility functions for the logic puzzle evaluation system."""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Any, Dict
import os


def setup_logging(log_file: Path, logger_name: str = None) -> logging.Logger:
    """Set up logging to file with unique logger per path.

    Args:
        log_file: Path to the log file
        logger_name: Unique name for the logger (defaults to log_file path)
    """
    if logger_name is None:
        logger_name = str(log_file)

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
    file_handler.setFormatter(file_formatter)

    logger.addHandler(file_handler)

    return logger


def create_result_directory(model_name: str) -> Path:
    """Create and return the results directory for a model."""
    # Sanitize model name for filesystem
    safe_model_name = model_name.replace('/', '_').replace('\\', '_')
    result_dir = Path('results') / safe_model_name
    result_dir.mkdir(parents=True, exist_ok=True)
    return result_dir


def get_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.utcnow().strftime('%Y%m%d_%H%M%S')


def save_json(data: Dict[str, Any], file_path: Path) -> None:
    """Save data to JSON file with pretty printing."""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)


def load_env() -> None:
    """Load environment variables from .env file if it exists."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass


def get_api_key() -> str:
    """Get OpenRouter API key from environment."""
    api_key = os.getenv('OPEN_ROUTER_TOKEN')
    if not api_key:
        raise ValueError(
            "OPEN_ROUTER_TOKEN environment variable not found. "
            "Please set it with your OpenRouter API key."
        )
    return api_key
