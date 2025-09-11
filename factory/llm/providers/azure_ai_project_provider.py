"""
Azure AI Project Provider.

This module defines the provider implementation for Azure AI Project-based
chat completions. It adapts the Azure AI Project SDK client to the
`LLMProviderBase` interface, adding retry logic, telemetry, and usage
extraction through `LLMClientHelper`.

Classes:
    AzureAIProjectProvider: Provider implementation for Azure AI Project.

Example:
    >>> from azure.ai.projects.aio import AIProjectClient
    >>> from src.factory.utils.utility import _get_azure_credential
    >>> from src.factory.llm.azure_ai_project_provider import AzureAIProjectProvider
    >>> from src.factory.llm.llm_model_config import LLM_MODELS
    >>>
    >>> credential = _get_azure_credential(api_key="<your-api-key>")
    >>> client = AIProjectClient(endpoint="https://<endpoint>", credential=credential)
    >>> model_config = LLM_MODELS["gpt-4o"]
    >>> provider = AzureAIProjectProvider(client, model_config)
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

from .base_provider import LLMProviderBase
from ..client_helper import LLMClientHelper
from factory.llm.llm_model_config import LLMModelConfig
from factory.logger.telemetry import telemetry


# Get a logger and tracer
logger = telemetry.get_logger(__name__)
tracer = telemetry.get_tracer(__name__)


class AzureAIProjectProvider(LLMProviderBase):
    """
    LLM provider for Azure AI Project (chat completions).

    Integrates with `LLMModelConfig` to ensure only supported arguments
    are passed into the request payload. Handles retries and telemetry
    for resiliency in production environments.
    """

    def __init__(self, client: Any, model_config: LLMModelConfig):
        """
        Initialize the Azure AI Project provider.

        Args:
            client (Any): An instance of `AIProjectClient`.
            model_config (LLMModelConfig): Model metadata and capabilities.
        """
        super().__init__(model_config, "azure-ai-project")
        self.client = client
        self.model_config = model_config

    async def get_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        **kwargs: Any,
    ) -> Union[str, Tuple[str, Dict[str, Any]]]:
        """
        Generate a chat completion using Azure AI Project.

        Args:
            system_prompt (str): System context message for the model.
            user_prompt (str): User input message.
            **kwargs (Any): Additional runtime arguments (temperature,
                reasoning, max_completion_tokens, response_format, tools, etc.).
                Only supported arguments (as per `LLMModelConfig`) are injected.

        Returns:
            str: Model output as plain text.
            Tuple[str, Dict[str, Any]]: If return_usage=True, returns both the
            output and usage statistics.

        Raises:
            Exception: Any error raised by the underlying client, after retries.
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

        # Adapt to Azure AI Project "messages" format
        request_payload["messages"] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        async def _call():
            return await self.client.agents.create_agent(**request_payload)

        response = await LLMClientHelper.run_with_retry(_call)

        # Extract text safely
        try:
            content = response.choices[0].message.content.strip()
        except Exception as e:
            logger.error("Failed to parse completion response: %s", e, exc_info=True)
            raise

        if kwargs.get("return_usage"):
            usage = LLMClientHelper.extract_usage(response)
            return content, usage

        return content
