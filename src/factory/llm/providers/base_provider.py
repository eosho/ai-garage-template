"""
LLM Provider Base Module.

This module defines the abstract base class `LLMProviderBase`, which enforces
a consistent interface for all Large Language Model (LLM) providers.

Each provider wraps its underlying client (Azure AI Project, Azure Inference,
OpenAI, etc.) and uses `LLMModelConfig` to ensure only supported features are
injected into requests.

Responsibilities:
    * Provide a normalized interface (`get_completion`) across providers.
    * Encapsulate model metadata via `LLMModelConfig`.
    * Allow flexible **kwargs for provider-specific parameters, while validating
      against supported features in `LLMModelConfig`.
    * Enable consistent telemetry and usage reporting.

Example:
    >>> from src.factory.llm.openai_provider import OpenAIProvider
    >>> from openai import AsyncOpenAI
    >>> from src.factory.llm.llm_model_config import LLM_MODELS
    >>>
    >>> client = AsyncOpenAI(api_key="<your-api-key>")
    >>> model_config = LLM_MODELS["gpt-4o"]
    >>> provider = OpenAIProvider(client, model_config)
    >>> response, usage = await provider.get_completion(
    ...     system_prompt="You are a helpful assistant.",
    ...     user_prompt="What's the weather in Paris?",
    ...     max_completion_tokens=100,
    ...     tools=[{"type": "function", "function": {"name": "get_weather"}}],
    ...     return_usage=True,
    ... )
    >>> print(response)
    {'content': 'It looks like Paris will be sunny today.', 'usage': {...}}
"""

from abc import ABC, abstractmethod
from typing import Any, Union, Tuple, Dict
from ..llm_model_config import LLMModelConfig


class LLMProviderBase(ABC):
    """
    Abstract base class for LLM providers.

    Attributes:
        model_config (LLMModelConfig): Metadata and capabilities of the model.
        model_name (str): Shortcut for `model_config.name`.
        provider_type (str): Logical provider type (e.g., 'azure-ai-project', 'azure-ai-inference', 'openai').
        client (Any): The underlying SDK client (e.g., AsyncOpenAI, AIProjectClient).
    """

    client: Any  # Declared so type checkers know every provider has a client

    def __init__(self, model_config: LLMModelConfig, provider_type: str) -> None:
        """
        Initialize a provider.

        Args:
            model_config (LLMModelConfig): Model metadata and capabilities.
            provider_type (str): Provider type string for telemetry/logging.
        """
        self.model_config = model_config
        self.model_name = model_config.name
        self.provider_type = provider_type

    @abstractmethod
    async def get_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        **kwargs: Any,
    ) -> Union[str, Dict[str, Any], Tuple[str, Dict[str, Any]]]:
        """
        Generate a completion using system and user prompts.

        Args:
            system_prompt (str): System context message for the model.
            user_prompt (str): User input message.
            **kwargs (Any): Optional runtime parameters, such as:
                - max_completion_tokens (int): Maximum number of tokens for output.
                - reasoning (bool): Enable reasoning mode (if supported).
                - response_format (Any): Structured response format (e.g., JSON schema).
                - tools (list[dict]): Tool definitions for function calling.
                - return_usage (bool): Whether to also return token usage.
                - temperature, top_p, frequency_penalty, etc.

        Returns:
            Union[str, Dict, Tuple[str, Dict]]:
                - str: Model output as plain text.
                - dict: Tool-call payload if tool calling is used.
                - tuple: (output, usage) if return_usage=True.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement `get_completion`."
        )
