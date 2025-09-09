# model_config.py

"""
LLM Model Configuration Module.

This module provides a systematic way to describe, validate, and use
capabilities of supported Large Language Models (LLMs) in the application.

It introduces `LLMModelConfig` as a metadata wrapper that describes:
    - The model's name, provider type, and version.
    - The features the model supports (e.g., reasoning, function calling,
      structured outputs, vision, prompt caching).
    - A utility for building request payloads that only includes supported
      parameters (avoiding API errors when calling unsupported features).

Features:
    * Centralized configuration for model capabilities.
    * Eliminates hard-coding of feature support across the codebase.
    * Provides validation and error logging when unsupported arguments
      are attempted.
    * Works across multiple provider types (Azure AI Project, Azure OpenAI,
      OpenAI, etc.).

Classes:
    LLMModelConfig:
        Encapsulates model metadata and feature support with utilities for
        safe request construction.

Globals:
    LLM_MODELS (Dict[str, LLMModelConfig]):
        Registry of known models and their supported features.

Usage Example:
    >>> from src.factory.llm.llm_model_config import LLM_MODELS
    >>> gpt5 = LLM_MODELS["gpt-5"]
    >>> request = gpt5.build_request_args(
    ...     max_completion_tokens=2048,
    ...     stream=True
    ... )
    >>> print(request)
    {
        'model': 'gpt-5',
        'max_completion_tokens': 2048,
        'stream': True
    }
"""

from typing import Any, Dict, Any, Literal, Optional, Union
from src.factory.logger.telemetry import LoggingFactory

# Initialize telemetry/logging
logging_factory = LoggingFactory()
logger = logging_factory.get_logger(__name__)


# Default features available across *all* chat completion models
DEFAULT_FEATURES: Dict[str, type | tuple[type, ...]] = {
    "seed": int,
    "response_format": object,  # can be JSON schema (dict) or "json"
    "max_tokens": int,
    "stream": bool,
    "max_completion_tokens": int,
}


class LLMModelConfig:
    """Encapsulates metadata and supported features for a specific LLM model."""

    def __init__(
        self,
        name: str,
        version: str,
        features: Dict[str, type | tuple[type, ...]],
    ) -> None:
        self.name = name
        self.version = version
        self.features = features

    def supports(self, feature: str) -> bool:
        """
        Check if the model supports a specific feature.

        Args:
            feature (str): The feature name (e.g., "reasoning").

        Returns:
            bool: True if the feature is supported, False otherwise.
        """
        return feature in self.features

    def build_request_args(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Build a request payload for the completion API, injecting only
        supported arguments.

        Args:
            prompt (str): The user prompt to send to the model.
            **kwargs (Any): Arbitrary arguments (e.g., max_completion_tokens,
                reasoning, temperature). Only supported arguments will be used.

        Returns:
            Dict[str, Any]: Sanitized request payload.

        Example:
            >>> gpt4o = LLM_MODELS["gpt-4o"]
            >>> request = gpt4o.build_request_args(
            ...     prompt="Translate to French: Hello",
            ...     temperature=0.7
            ... )
            >>> print(request)
            {
                'model': 'gpt-4o',
                'temperature': 0.7,
            }
        """
        request: Dict[str, Any] = {"model": self.name}

        for key, value in kwargs.items():
            if value is None or key in "return_usage":
                continue
            if key in self.features:
                expected_type = self.features[key]
                if not isinstance(value, expected_type):
                    logger.error(
                        "Invalid type for feature '%s' in model=%s: expected %s, got %s",
                        key, self.name, expected_type, type(value)
                    )
                    raise TypeError(f"Feature '{key}' must be of type {expected_type}, got {type(value)}")
                request[key] = value
                logger.debug("Accepted feature '%s' with value=%s for model=%s", key, value, self.name)
            else:
                logger.warning("Ignored unsupported argument '%s' for model=%s", key, self.name)

        return request



# -------------------------------------------------------------------------
# Builder Utility
# -------------------------------------------------------------------------
def build_model(name: str, version: str, extra: Dict[str, Any]) -> LLMModelConfig:
    """
    Create an `LLMModelConfig` by merging default features with model-specific ones.

    Args:
        name (str): Model identifier (e.g., "gpt-5").
        version (str): API version string.
        extra (Dict[str, Any]): Additional features and their expected types.

    Returns:
        LLMModelConfig: Config object with combined features.
    """
    return LLMModelConfig(name, version, {**DEFAULT_FEATURES, **extra})


# -------------------------------------------------------------------------
# Registry of Supported Models
# -------------------------------------------------------------------------

LLM_MODELS: Dict[str, LLMModelConfig] = {
    # GPT-5
    "gpt-5": build_model(
        name="gpt-5",
        version="2025-03-01",
        extra={
            "reasoning_effort": str,
            "tools": object,
            "tool_choice": str, # none, auto, required
            "parallel_tool_calls": bool,
        },
    ),

    # GPT-4o
    "gpt-4o": build_model(
        name="gpt-4o",
        version="2024-12-01",
        extra={
            **DEFAULT_FEATURES,
            "temperature": float,
            "top_p": float,
            "tool_choice": object,
            "tools": object
        },
    ),
    
    # Support more
}
