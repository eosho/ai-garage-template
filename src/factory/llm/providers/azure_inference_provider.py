"""
Azure AI Inference Provider.

This module defines the provider implementation for Azure AI Inference-based
chat completions. It adapts the Azure AI Inference SDK client to the
`LLMProviderBase` interface, adding retry logic, telemetry, and usage
extraction through `LLMClientHelper`.

Classes:
    AzureInferenceProvider: Provider implementation for Azure AI Inference.

Example:
    >>> from azure.ai.inference.aio import ChatCompletionsClient
    >>> from src.factory.utils.utility import _get_azure_credential
    >>> from src.factory.llm.azure_inference_provider import AzureInferenceProvider
    >>> from src.factory.llm.llm_model_config import LLM_MODELS
    >>>
    >>> credential = _get_azure_credential(api_key="<your-api-key>")
    >>> client = ChatCompletionsClient(
    ...     endpoint="https://<endpoint>",
    ...     credential=credential,
    ...     api_version="2024-12-01",
    ... )
    >>> model_config = LLM_MODELS["gpt-4o"]
    >>> provider = AzureInferenceProvider(client, model_config)
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


class AzureInferenceProvider(LLMProviderBase):
    """
    LLM provider for Azure AI Inference (chat + completion).

    Integrates with `LLMModelConfig` to ensure only supported arguments
    are passed into the request payload. Handles retries and telemetry
    for resiliency in production environments.
    """

    def __init__(self, client: Any, model_config: LLMModelConfig):
        """
        Initialize the Azure AI Inference provider.

        Args:
            client (Any): An instance of `ChatCompletionsClient`.
            model_config (LLMModelConfig): Model metadata and capabilities.
        """
        super().__init__(model_config, "azure-ai-inference")
        self.client = client
        self.model_config = model_config

    async def get_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        **kwargs: Any,
    ) -> Union[str, Tuple[str, Dict[str, Any]]]:
        """
        Generate a completion using system and user prompts.

        Args:
            system_prompt (str): System context message for the model.
            user_prompt (str): User input message, which can be plain text
                or multimodal (e.g., text + image).
            **kwargs (Any): Optional runtime parameters, including:
                - max_completion_tokens (int): Maximum tokens for the response.
                - reasoning (bool): Enable reasoning mode (if supported).
                - response_format (Any): Structured response format (e.g., JSON schema).
                - tools (list[dict]): Tool/function definitions for function calling.
                - return_usage (bool): If True, return a tuple (output, usage).

        Returns:
            str: Model output as plain text.
            Tuple[str, Dict[str, Any]]: If return_usage=True, returns both output and usage.

        Raises:
            ValueError: If the response is empty.
            Exception: Propagates any SDK or runtime errors after retries.
        """
        # Build request using model-aware configuration
        request_payload = self.model_config.build_request_args(**kwargs)

        # Adapt to Azure Inference "messages" format
        request_payload["messages"] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        logger.info(
            "Request payload for Azure Inference model=%s: %s",
            self.model_config.name, request_payload
        )

        async def _call():
            return await self.client.complete(**request_payload)

        response = await LLMClientHelper.run_with_retry(_call)
        if response is None:
            raise ValueError("No response received from Azure AI Inference")

        try:
            content = response.choices[0].message.content.strip()
        except Exception as e:
            logger.error("Failed to parse completion response: %s", e, exc_info=True)
            raise

        if kwargs.get("return_usage"):
            usage = LLMClientHelper.extract_usage(response)
            return content, usage

        return content
