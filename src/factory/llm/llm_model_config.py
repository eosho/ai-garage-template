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
    ...     prompt="Explain quantum computing simply.",
    ...     max_completion_tokens=2048,
    ...     reasoning=True
    ... )
    >>> print(request)
    {
        'model': 'gpt-5',
        'prompt': 'Explain quantum computing simply.',
        'max_completion_tokens': 2048,
        'reasoning': True
    }
"""

import json
from typing import Set, Dict, Any, Optional
from src.factory.logger.telemetry import LoggingFactory

# Initialize telemetry/logging
logging_factory = LoggingFactory()
logger = logging_factory.get_logger(__name__)


class LLMModelConfig:
    """
    Encapsulates metadata and supported features for a specific LLM model.

    Responsibilities:
        - Store metadata (model name, provider type, version).
        - Track supported features for safe runtime configuration.
        - Validate requested parameters against supported features.
        - Build request payloads for completion APIs.

    Attributes:
        name (str): Model identifier (e.g., "gpt-5", "gpt-4o").
        version (str): API version or deployment version.
        features (Set[str]): Set of supported features (e.g.,
            {"reasoning", "function_calling"}).

    Example:
        >>> config = LLMModelConfig(
        ...     name="gpt-5",
        ...     version="2025-03-01",
        ...     features={"reasoning", "function_calling"}
        ... )
        >>> config.supports("reasoning")
        True
    """

    def __init__(
        self,
        name: str,
        version: str,
        features: Set[str],
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
            ...     temperature=0.7,
            ...     reasoning=True
            ... )
            >>> print(request)
            {
                'model': 'gpt-4o',
                'temperature': 0.7,
                'reasoning': True
            }
        """
        request: Dict[str, Any] = {"model": self.name}

        for key, value in kwargs.items():
            if value is None:
                continue
            if key in self.features or key in {"temperature", "top_p"}:
                request[key] = value
                logger.debug(
                    "Accepted feature '%s' with value=%s for model=%s",
                    key, value, self.name
                )
            else:
                logger.warning(
                    "Ignored unsupported argument '%s' for model=%s",
                    key, self.name
                )

        return request


# -------------------------------------------------------------------------
# Registry of supported models
# This should be populated from configuration, database, or API in real use.
# For now, defaults are provided as a baseline.
# -------------------------------------------------------------------------

LLM_MODELS: Dict[str, LLMModelConfig] = {
    # GPT-5 (reasoning + advanced features)
    "gpt-5": LLMModelConfig(
        name="gpt-5",
        version="2025-03-01",
        features={
            "reasoning",
            "max_completion_tokens",
            "function_calling",
            "response_format",
            "prompt_caching",
            "json_mode",
            "reproducible_output",
        },
    ),

    # GPT-4o (multimodal + reasoning)
    "gpt-4o": LLMModelConfig(
        name="gpt-4o",
        version="2024-12-01",
        features={
            "reasoning",
            "max_completion_tokens",
            "function_calling",
            "vision",
            "max_tokens",
            "response_format",
            "json_mode",
        },
    ),

    # GPT-4o mini (lighter multimodal)
    "gpt-4o-mini": LLMModelConfig(
        name="gpt-4o-mini",
        version="2024-12-01",
        features={
            "reasoning",
            "max_completion_tokens",
            "function_calling",
            "vision",
            "json_mode",
        },
    ),

    # o4-mini (fast multimodal)
    "o4-mini": LLMModelConfig(
        name="o4-mini",
        version="2024-11-01",
        features={
            "reasoning",
            "max_completion_tokens",
            "function_calling",
            "vision",
        },
    ),

    # o3-mini (smaller reasoning)
    "o3-mini": LLMModelConfig(
        name="o3-mini",
        version="2024-10-01",
        features={
            "reasoning",
            "max_completion_tokens",
            "function_calling",
        },
    ),

    # o3 (larger reasoning)
    "o3": LLMModelConfig(
        name="o3",
        version="2024-10-01",
        features={
            "reasoning",
            "max_completion_tokens",
            "function_calling",
        },
    ),
}
