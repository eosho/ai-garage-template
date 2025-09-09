"""
OpenAI Provider.

This module defines the provider implementation for OpenAI’s API
(chat completions). It adapts the OpenAI SDK client to the
`LLMProviderBase` interface, adding retry logic, telemetry,
and usage extraction through `LLMClientHelper`.

Classes:
    OpenAIProvider: Provider implementation for OpenAI API.

Example:
    >>> from openai import AsyncOpenAI
    >>> from src.factory.llm.openai_provider import OpenAIProvider
    >>> from src.factory.llm.llm_model_config import LLM_MODELS
    >>>
    >>> client = AsyncOpenAI(api_key="<your-api-key>")
    >>> model_config = LLM_MODELS["gpt-4o"]
    >>> provider = OpenAIProvider(client, model_config)
    >>> response, usage = await provider.get_completion(
    ...     system_prompt="You are a helpful assistant.",
    ...     user_prompt="Explain observability in one sentence.",
    ...     max_completion_tokens=50,
    ...     return_usage=True,
    ... )
    >>> print(response)
    "Observability is the ability to understand a system's internal state
     by examining its external outputs."
"""

from typing import Any, Dict, Tuple, Union

from src.factory.logger.telemetry import LoggingFactory
from ..base_provider import LLMProviderBase
from ..client_helper import LLMClientHelper
from src.factory.llm.llm_model_config import LLMModelConfig

logging_factory = LoggingFactory()
logger = logging_factory.get_logger(__name__)


class OpenAIProvider(LLMProviderBase):
    """
    LLM provider for OpenAI API.

    Integrates with `LLMModelConfig` to ensure only supported arguments
    are passed into the request payload. Handles retries and telemetry
    for resiliency in production environments.
    """

    def __init__(self, client: Any, model_config: LLMModelConfig):
        """
        Initialize the OpenAI provider.

        Args:
            client (Any): An instance of `AsyncOpenAI`.
            model_config (LLMModelConfig): Model metadata and capabilities.
        """
        super().__init__(model_config, "openai")
        self.client = client
        self.model_config = model_config

    async def get_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        **kwargs: Any,
    ) -> Union[str, Tuple[str, Dict[str, Any]]]:
        """
        Generate a chat completion using OpenAI.

        Args:
            system_prompt (str): System context message for the model.
            user_prompt (str): User input message (plain text or multimodal).
            **kwargs (Any): Optional runtime parameters, including:
                - max_completion_tokens (int): Maximum number of tokens for the response.
                - reasoning (bool): Enable reasoning mode (if supported).
                - response_format (Any): Structured response format (e.g., JSON schema).
                - tools (list[dict]): Tool/function definitions for function calling.
                - return_usage (bool): If True, return (output, usage).
                - temperature, top_p, frequency_penalty, etc.

        Returns:
            str: Model output as plain text.
            Tuple[str, Dict[str, Any]]: If return_usage=True, returns both output and usage.

        Raises:
            Exception: Propagates any SDK or runtime errors after retries.
        """
        # Build request using model-aware configuration
        request_payload = self.model_config.build_request_args(
            prompt=user_prompt,
            temperature=kwargs.get("temperature", 0.7),
            max_completion_tokens=kwargs.get("max_completion_tokens"),
            reasoning=kwargs.get("reasoning"),
            response_format=kwargs.get("response_format"),
            tools=kwargs.get("tools"),
        )

        # Adapt to OpenAI "chat.completions.create" format
        request_payload["model"] = self.model_config.name
        request_payload["messages"] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        async def _call():
            return await self.client.chat.completions.create(**request_payload)

        response = await LLMClientHelper.run_with_retry(_call)

        try:
            content = response.choices[0].message.content.strip()
        except Exception as e:
            logger.error("Failed to parse completion response: %s", e, exc_info=True)
            raise

        if kwargs.get("return_usage"):
            usage = LLMClientHelper.extract_usage(response)
            return content, usage

        return content
