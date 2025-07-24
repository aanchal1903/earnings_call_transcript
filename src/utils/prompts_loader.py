"""
Prompt management utilities for the Structured RAG Agent:
    - Provides a centralized way to load and cache YAML-based instruction prompts,
      ensuring they are decoupled from application logic and easily maintainable.
"""
import yaml
import logging
from pathlib import Path
from functools import lru_cache
from typing import Dict, Any
from config.config import PROJECT_ROOT

logger = logging.getLogger(__name__)

PROMPTS_DIR = PROJECT_ROOT / "src" / "prompts"

@lru_cache(maxsize=10)
def load_prompt_file(filename: str) -> Dict[str, Any]:
    """
    Loads and parses a YAML prompt file from this agent's prompts directory.

    Args:
        filename: The name of the YAML file to load (e.g., 'data_router_prompt.yaml').

    Returns:
        A dictionary representing the parsed content of the YAML file.
    """
    prompt_path = PROMPTS_DIR / filename
    logger.debug(f"Loading prompt file: {prompt_path}")

    if not prompt_path.exists():
        logger.error(f"Prompt file not found: {prompt_path}")
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not data:
            raise ValueError(f"Prompt file is empty or invalid: {prompt_path}")
        return data
    except yaml.YAMLError as exc:
        logger.error(f"YAML parsing error in {prompt_path}: {exc}")
        raise ValueError(f"Error parsing YAML from {prompt_path}") from exc