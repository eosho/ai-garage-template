# azure_ai_project_provider.py
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
    >>> from factory.llm.azure_ai_project_provider import AzureAIProjectProvider
    >>>
    >>> credential = _get_azure_credential(api_key="<your-api-key>")
    >>> client = AIProjectClient(endpoint="https://<endpoint>", credential=credential)
    >>> provider = AzureAIProjectProvider(client, "gpt-4o")
    >>> response, usage = await provider.get_completion(
    ...     system_prompt="You are a helpful assistant.",
    ...     user_prompt="Explain observability in one sentence.",
    ...     max_tokens=50,
    ...     return_usage=True,
    ... )
    >>> print(response)
    "Observability is the ability to understand a system's internal state
     by examining its external outputs."
"""

from typing import Any, Dict, Optional, Tuple, Union

from src.factory.logger.telemetry import LoggingFactory
from ..base_provider import LLMProviderBase
from ..client_helper import LLMClientHelper

logging_factory = LoggingFactory()
logger = logging_factory.get_logger(__name__)


class AzureAIProjectProvider(LLMProviderBase):
    """
    LLM provider for Azure AI Project (chat completions).
    """

    def __init__(self, client: Any, deployment_name: str):
        super().__init__(deployment_name, "azure-ai-project")
        self.client = client

    async def get_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        **kwargs: Any,
    ) -> Any:
        """
        Generate a chat completion using Azure AI Project.

        Args:
            system_prompt (str): System context message for the model.
            user_prompt (str): User input message.
            max_tokens (int): Maximum tokens for the response.
            response_format (Optional[Any]): Optional structured response format.
            tools (Optional[Any]): Optional tool definitions (if supported in future).
            return_usage (bool): If True, also return token usage statistics.

        Returns:
            Any: The model's response, which can be a string, dict, or tuple.
                - Model output as text (str).
                - Or tool-call payload (dict) if tool calling supported later.
                - Or tuple (output, usage) if return_usage=True.
        """
        params = {
            "temperature": 0.7,
            "model": self.deployment_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        if kwargs.get("response_format") is not None:
            params["response_format"] = kwargs["response_format"]

        if kwargs.get("tools") is not None:
            params["tools"] = kwargs["tools"]

        if kwargs.get("max_tokens") is not None:
            params["max_tokens"] = kwargs["max_tokens"]

        async def _call():
            return await self.client.agents.create_agent(**params)

        response = await LLMClientHelper.run_with_retry(_call)
        content = response.choices[0].message.content.strip()

        if kwargs.get("return_usage"):
            return content, LLMClientHelper.extract_usage(response)
        return content