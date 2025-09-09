# base_provider.py

"""
LLM Provider Base Module.

This module defines the abstract base class `LLMProviderBase`, which enforces
a consistent interface for all Large Language Model (LLM) providers.

Each provider must implement its own `get_completion` method. Additional
parameters such as max_tokens, temperature, response_format, tools, or
return_usage are passed via **kwargs, keeping the interface flexible.

Example:
    >>> from factory.llm.openai_provider import OpenAIProvider
    >>> from openai import AsyncOpenAI
    >>> client = AsyncOpenAI(api_key="<your-api-key>")
    >>> provider = OpenAIProvider(client, "gpt-4o")
    >>> response = await provider.get_completion(
    ...     system_prompt="You are a helpful assistant.",
    ...     user_prompt="What's the weather in Paris?",
    ...     max_tokens=100,
    ...     tools=[{"type": "function", "function": {"name": "get_weather"}}],
    ...     return_usage=True,
    ... )
    >>> print(response)
    {'content': 'It looks like Paris will be sunny today.', 'usage': {...}}
"""

from abc import ABC, abstractmethod
from typing import Any


class LLMProviderBase(ABC):
    """
    Abstract base class for LLM providers.

    Attributes:
        deployment_name (str): Name of the deployment/model.
        provider_type (str): Provider type (e.g., 'azure-ai-project', 'openai').
        client (Any): The underlying SDK client (e.g., AsyncOpenAI, AIProjectClient).
    """

    client: Any  # Declared here so type checkers know it exists

    def __init__(self, deployment_name: str, provider_type: str) -> None:
        self.deployment_name = deployment_name
        self.provider_type = provider_type

    @abstractmethod
    async def get_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        **kwargs: Any,
    ) -> Any:
        """
        Generate a completion using system and user prompts.

        Args:
            system_prompt (str): System context message for the model.
            user_prompt (str): User input message.
            **kwargs (Any): Optional provider-specific parameters, such as:
                - max_tokens (int): Maximum number of tokens for the output.
                - response_format (Any): Structured response format (e.g., JSON schema).
                - tools (list[dict]): Tool definitions for function calling.
                - return_usage (bool): Whether to also return token usage.
                - temperature, top_p, frequency_penalty, etc.

        Returns:
            Any: The model's response. Typically one of:
                - str: Model output as plain text.
                - dict: Tool-call payload.
                - tuple: (output, usage) if return_usage=True.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement `get_completion`."
        )
