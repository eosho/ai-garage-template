"""
Constants Module.

This module defines constants used throughout the LLM Provider and related
factories. It centralizes configuration keys, model-specific behavior, and
paths for secret management, ensuring consistency across the codebase.

Features:
    * Standardized environment variable names for Azure OpenAI and OpenAI.
    * Default values for Azure identity credentials (tenant, client ID, secret).
    * Model-specific behavior sets (e.g., models that require
      `max_completion_tokens` instead of `max_tokens`).
    * Path configuration for filesystem-based secrets (e.g., `/etc/secrets`).

Usage:
    >>> import os
    >>> from factory.llm.constants import CONFIGURATION_NAME_OPENAI_API_KEY
    >>> api_key = os.getenv(CONFIGURATION_NAME_OPENAI_API_KEY)
    >>> print(api_key)
    "sk-abc123..."
"""

from typing import Literal, Set

AKEYLESS_SECRETS_PATH = "/etc/secrets"

MODELS_WITH_MAX_COMPLETION_TOKENS: Set[str] = {
    "o1-preview", "o1-mini", "o4-mini", "o3-mini",
    "o3", "gpt-4o", "gpt-4o-mini", "gpt-5"
}

MEMORY_PROVIDERS: Set[str] = {
    "cosmosdb", "json"
}

DEFAULT_MEMORY_PROVIDER = "json"

DEFAULT_PROVIDER_TYPE: Literal["azure-ai-project", "azure-ai-inference", "azure_openai"] = "azure-ai-project"

DEFAULT_AZURE_TENANT_ID = "AZURE_TENANT_ID"
DEFAULT_AZURE_CLIENT_ID = "AZURE_CLIENT_ID"
DEFAULT_AZURE_CLIENT_SECRET = "AZURE_CLIENT_SECRET"

CONFIGURATION_NAME_AZURE_OPENAI_MODEL_NAME = "AZURE_OPENAI_MODEL_NAME"
CONFIGURATION_NAME_AZURE_OPENAI_API_KEY = "AZURE_OPENAI_API_KEY"
CONFIGURATION_NAME_AZURE_OPENAI_ENDPOINT = "AZURE_OPENAI_ENDPOINT"
CONFIGURATION_NAME_AZURE_OPENAI_API_VERSION = "AZURE_OPENAI_API_VERSION"
CONFIGURATION_NAME_AZURE_OPENAI_DEPLOYMENT_NAME = "AZURE_OPENAI_DEPLOYMENT_NAME"

CONFIGURATION_NAME_AZURE_AI_INFERENCE_CHAT_ENDPOINT = "AZURE_AI_INFERENCE_CHAT_ENDPOINT"

CONFIGURATION_NAME_OPENAI_MODEL_NAME = "OPENAI_MODEL_NAME"
CONFIGURATION_NAME_OPENAI_API_KEY = "OPENAI_API_KEY"
CONFIGURATION_NAME_OPENAI_ENDPOINT = "OPENAI_ENDPOINT"
CONFIGURATION_NAME_OPENAI_API_VERSION = "OPENAI_API_VERSION"

CONFIGURATION_NAME_APPLICATIONINSIGHTS_CONNECTION_STRING = "APPLICATIONINSIGHTS_CONNECTION_STRING"

CONFIGURATION_NAME_COSMOS_DB_ENDPOINT = "COSMOS_DB_ENDPOINT"
CONFIGURATION_NAME_COSMOS_DB_KEY = "COSMOS_DB_KEY"