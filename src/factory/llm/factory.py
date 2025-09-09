# factory.py

"""
LLM Provider Module.

This module defines the provider abstractions for interacting with different
LLM backends (Azure AI Project, Azure AI Inference, OpenAI, etc.). Each provider
wraps its respective client SDK and exposes a unified interface for generating
completions, with built-in:

    * Normalized input/output formats across providers.
    * Optional usage statistics for token and cost tracking.
    * Telemetry integration with logging and tracing.

Classes:
    LLMProviderBase: Abstract base class defining the common provider interface.
    AzureAIProvider: Provider implementation for Azure AI Project (chat completions).
    AzureInferenceProvider: Provider implementation for Azure AI Inference.
    OpenAIProvider: Provider implementation for OpenAI’s public API.

Usage:
    >>> from factory.llm.openai_provider import OpenAIProvider
    >>> from openai import AsyncOpenAI
    >>> client = AsyncOpenAI(api_key="<your-api-key>")
    >>> provider = OpenAIProvider(client, "gpt-4o")
    >>> response = await provider.get_completion(
    ...     system_prompt="You are a helpful assistant.",
    ...     user_prompt="Explain observability in one sentence.",
    ...     max_tokens=50
    ... )
    >>> print(response)
    "Observability is the ability to understand a system's internal state
     by examining its external outputs."
"""

from openai import AsyncAzureOpenAI
from azure.ai.projects.aio import AIProjectClient
from azure.ai.inference.aio import ChatCompletionsClient

from src.factory.logger.telemetry import LoggingFactory
from src.factory.config.app_config import config
from src.factory.utils.utility import _get_azure_credential

from .base_provider import LLMProviderBase
from .providers.azure_inference_provider import AzureInferenceProvider
from .providers.openai_provider import OpenAIProvider
from .providers.azure_ai_project_provider import AzureAIProjectProvider


logging_factory = LoggingFactory()
logger = logging_factory.get_logger(__name__)
tracer = logging_factory.get_tracer(__name__)



class LLMFactory:
    """Factory for creating LLM providers based on configuration."""

    @staticmethod
    def _create_azure_inference_provider(
        api_key: str,
        endpoint: str,
        deployment_name: str,
        api_version: str
    ) -> AzureInferenceProvider:
        """Create a provider for Azure AI Inference.

        Args:
            api_key (str): API key for authentication.
            endpoint (str): Endpoint URL for the Azure AI Inference service.
            deployment_name (str): Deployment name or model identifier.
            api_version (str): API version to use.

        Returns:
            AzureInferenceProvider: Configured Azure AI Inference provider instance.
        """
        credential = _get_azure_credential(api_key=api_key)
        client = ChatCompletionsClient(
            endpoint=endpoint,
            credential=credential,
            api_version=api_version,
        )
        logger.info("Created Azure AI Inference provider for deployment=%s", deployment_name)
        return AzureInferenceProvider(client, deployment_name)

    @staticmethod
    def _create_openai_provider(api_key: str, deployment_name: str) -> OpenAIProvider:
        """Create a provider for OpenAI API.

        Args:
            api_key (str): API key for OpenAI.
            deployment_name (str): Model name or identifier.

        Returns:
            OpenAIProvider: Configured OpenAI provider instance.
        """
        client = AsyncAzureOpenAI(api_key=api_key)
        logger.info("Created OpenAI provider for model=%s", deployment_name)
        return OpenAIProvider(client, deployment_name)

    @staticmethod
    def _create_ai_project_provider(
        api_key: str,
        endpoint: str,
        deployment_name: str,
        ) -> AzureAIProjectProvider:
        """Create a provider for Azure AI Project.

        Args:
            api_key (str): API key for authentication.
            endpoint (str): Endpoint URL for the Azure AI Project service.
            deployment_name (str): Deployment name or model identifier.

        Returns:
            LLMProviderBase: Configured Azure AI Project provider instance.
        """
        credential = _get_azure_credential(api_key=api_key)
        client = AIProjectClient(
            endpoint=endpoint,
            credential=credential,
        )
        logger.info("Created Azure AI Project provider for deployment=%s", deployment_name)
        return AzureAIProjectProvider(client, deployment_name)

    @staticmethod
    async def create_llm_provider() -> LLMProviderBase:
        """
        Detect provider type from config and return the appropriate provider instance.

        Returns:
            LLMProviderBase: Configured provider instance.
        """
        # Determine provider type from config
        provider_type = config.DEFAULT_PROVIDER
        logger.info("Creating LLM provider of type=%s", provider_type)

        # Common parameters
        api_key = config.AZURE_OPENAI_API_KEY
        endpoint = config.AZURE_OPENAI_ENDPOINT
        deployment_name = config.AZURE_OPENAI_DEPLOYMENT
        api_version = config.AZURE_OPENAI_API_VERSION

        # Create and return the appropriate provider instance
        if provider_type == "azure-ai-project":
            return LLMFactory._create_ai_project_provider(api_key, endpoint, deployment_name)

        elif provider_type == "azure-ai-inference":
            return LLMFactory._create_azure_inference_provider(api_key, endpoint, deployment_name, api_version)

        elif provider_type == "azure_openai":
            return LLMFactory._create_openai_provider(api_key, deployment_name)

        else:
            raise ValueError(f"Unsupported provider type: {provider_type}")
