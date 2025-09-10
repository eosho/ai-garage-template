"""
LLM Factory Module.

This module centralizes the creation of LLM provider instances across different
backends (Azure AI Project, Azure AI Inference, OpenAI). It integrates with
`LLMModelConfig` to ensure model-specific capabilities (reasoning, function
calling, structured outputs, etc.) are known and respected.

Providers:
    * AzureAIProjectProvider: Wraps the Azure AI Project SDK.
    * AzureInferenceProvider: Wraps the Azure AI Inference SDK.
    * OpenAIProvider: Wraps the OpenAI SDK.

Features:
    * Normalized input/output formats across providers.
    * Automatic selection of the appropriate provider type from config.
    * Uses `LLMModelConfig` to validate and inject supported arguments.
    * Built-in telemetry with structured logging and tracing.
    * Graceful error handling and explicit exceptions for unsupported models.

Classes:
    LLMFactory:
        Factory for instantiating provider classes given configuration and model metadata.

Usage:
    >>> from src.factory.llm.factory import LLMFactory
    >>> provider = await LLMFactory.create_llm_provider()
    >>> response = await provider.get_completion(
    ...     system_prompt="You are a helpful assistant.",
    ...     user_prompt="Summarize observability in one sentence.",
    ...     reasoning=True,
    ...     max_completion_tokens=200
    ... )
    >>> print(response)
    "Observability is the ability to understand a system's internal state
     by examining its external outputs."
"""

from typing import Optional
from openai import AsyncAzureOpenAI
from azure.ai.projects.aio import AIProjectClient
from azure.ai.inference.aio import ChatCompletionsClient

from src.factory.logger.telemetry import telemetry
from src.factory.config.app_config import config
from src.factory.utils.utility import _get_azure_credential
from src.factory.llm.llm_model_config import LLM_MODELS, LLMModelConfig

from .providers.base_provider import LLMProviderBase
from .providers.azure_inference_provider import AzureInferenceProvider
from .providers.openai_provider import OpenAIProvider
from .providers.azure_ai_project_provider import AzureAIProjectProvider




# Get a logger and tracer
logger = telemetry.get_logger(__name__)
tracer = telemetry.get_tracer(__name__)


class LLMFactory:
    """Factory for creating LLM providers based on configuration and model capabilities."""

    @staticmethod
    def _create_azure_inference_provider(
        api_key: str,
        endpoint: str,
        model_config: LLMModelConfig,
        api_version: str,
    ) -> AzureInferenceProvider:
        """
        Create a provider for Azure AI Inference.

        Args:
            api_key (str): API key for authentication.
            endpoint (str): Endpoint URL for the Azure AI Inference service.
            model_config (LLMModelConfig): Model metadata and capabilities.
            api_version (str): API version to use.

        Returns:
            AzureInferenceProvider: Configured Azure AI Inference provider instance.
        """
        credential = _get_azure_credential(api_key=api_key)
        client = ChatCompletionsClient(endpoint=endpoint, credential=credential, api_version=api_version)
        logger.info("Created Azure AI Inference provider for model=%s", model_config.name)
        return AzureInferenceProvider(client, model_config)

    @staticmethod
    def _create_openai_provider(
        api_key: str,
        model_config: LLMModelConfig,
    ) -> OpenAIProvider:
        """
        Create a provider for the OpenAI API.

        Args:
            api_key (str): API key for OpenAI authentication.
            model_config (LLMModelConfig): Model metadata and capabilities.

        Returns:
            OpenAIProvider: Configured OpenAI provider instance.
        """
        client = AsyncAzureOpenAI(api_key=api_key)
        logger.info("Created OpenAI provider for model=%s", model_config.name)
        return OpenAIProvider(client, model_config)

    @staticmethod
    def _create_ai_project_provider(
        api_key: str,
        endpoint: str,
        model_config: LLMModelConfig,
    ) -> AzureAIProjectProvider:
        """
        Create a provider for Azure AI Project.

        Args:
            api_key (str): API key for authentication.
            endpoint (str): Endpoint URL for the Azure AI Project service.
            model_config (LLMModelConfig): Model metadata and capabilities.

        Returns:
            AzureAIProjectProvider: Configured Azure AI Project provider instance.
        """
        credential = _get_azure_credential(api_key=api_key)
        client = AIProjectClient(endpoint=endpoint, credential=credential)
        logger.info("Created Azure AI Project provider for model=%s", model_config.name)
        return AzureAIProjectProvider(client, model_config)

    @staticmethod
    async def create_llm_provider() -> LLMProviderBase:
        """
        Detect provider type from AppConfig and return the appropriate provider instance.

        Returns:
            LLMProviderBase: Configured provider instance with model metadata.

        Raises:
            ValueError: If the provider type or model is unsupported.
        """
        provider_type = config.DEFAULT_PROVIDER
        model_name = config.AZURE_OPENAI_DEPLOYMENT

        logger.info("Creating LLM provider of type=%s model=%s", provider_type, model_name)

        model_config: Optional[LLMModelConfig] = LLM_MODELS.get(model_name)
        if not model_config:
            logger.error("Unsupported model requested: %s", model_name)
            raise ValueError(f"Unsupported model: {model_name}")

        api_key = config.AZURE_OPENAI_API_KEY
        endpoint = config.AZURE_OPENAI_ENDPOINT
        api_version = config.AZURE_OPENAI_API_VERSION

        if provider_type == "azure-ai-project":
            return LLMFactory._create_ai_project_provider(api_key, endpoint, model_config)

        elif provider_type == "azure-ai-inference":
            return LLMFactory._create_azure_inference_provider(api_key, endpoint, model_config, api_version)

        elif provider_type == "azure_openai":
            return LLMFactory._create_openai_provider(api_key, model_config)

        else:
            logger.error("Unsupported provider type: %s", provider_type)
            raise ValueError(f"Unsupported provider type: {provider_type}")
