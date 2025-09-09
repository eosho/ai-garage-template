# app_config.py

"""
Application Configuration Module.

This module centralizes how configuration values are loaded across the
application. It supports environment variables, `.env` files, and filesystem-
based secrets (e.g., mounted at `/etc/secrets` via Akeyless or Kubernetes).

Features:
    * Unified access to Azure OpenAI, Cosmos DB, and other settings.
    * Support for required and optional environment variables.
    * Automatic fallback order: environment → secret store → default value.
    * All values resolved at startup and cached as plain strings.
    * Built-in logging warnings for missing optional values.
    * Provides a global `config` instance for convenience.

Class:
    AppConfig:
        Loads all known configuration values into attributes on initialization.
        Each attribute is a plain string (never None). Optional values default
        to an empty string or a provided fallback.

Functions (internal):
    _resolve(name: str, required: bool = True, default: Optional[str] = None) -> str
        Resolves a config value from env, secrets, or default.
        Raises ValueError if required and not found.

Globals:
    config (AppConfig):
        Global singleton instance of AppConfig for reuse.

Example Usage:
    >>> from factory.config.app_config import config

    # Access Azure OpenAI configuration
    >>> print(config.AZURE_OPENAI_ENDPOINT)
    "https://my-resource.openai.azure.com/"

    >>> print(config.AZURE_OPENAI_DEPLOYMENT)
    "gpt-4o"

    # Access OpenAI API key
    >>> print(config.OPENAI_API_KEY)
    "sk-12345..."

    # Check if Application Insights is enabled
    >>> if config.APPLICATION_INSIGHTS_CONNECTION_STRING:
    ...     print("App Insights enabled")

    # Use in other services
    >>> from factory.llm.provider import LLMFactory
    >>> provider = await LLMFactory.create_llm_provider()
"""

import os
from typing import Optional, Literal, Set
from functools import lru_cache

from dotenv import (
    find_dotenv,
    load_dotenv
)

from .secret_config import get_secret
from src.factory.logger.telemetry import LoggingFactory

# Initialize telemetry (Azure Monitor if configured, otherwise fallback to console)
logging_factory = LoggingFactory()

# Get a logger and tracer
logger = logging_factory.get_logger(__name__)
tracer = logging_factory.get_tracer(__name__)

# Override dotenv values
load_dotenv(find_dotenv(), override=True)



# ---------------------------------------------------------------------------
# Global defaults / allowed values (moved here from constants.py)
# ---------------------------------------------------------------------------

# Default secrets directory
AKEYLESS_SECRETS_PATH = "/etc/secrets"

# Models that require `max_completion_tokens`
MODELS_WITH_MAX_COMPLETION_TOKENS: Set[str] = {
    "o1-preview", "o1-mini", "o4-mini", "o3-mini",
    "o3", "gpt-4o", "gpt-4o-mini", "gpt-5"
}

# Memory providers
MEMORY_PROVIDERS: Set[str] = {"cosmosdb", "json"}
DEFAULT_MEMORY_PROVIDER = "json"

# Provider types
DEFAULT_PROVIDER_TYPE: Literal["azure-ai-project", "azure-ai-inference", "azure_openai"] = "azure-ai-project"

print(os.environ.get("AZURE_TENANT_ID"))

@lru_cache(maxsize=1)
class AppConfig:
    """Centralized application configuration (all resolved to strings)."""

    def __init__(self) -> None:
        logger.info("Loading application configuration")

        # Azure Auth
        self.AZURE_TENANT_ID = self._resolve("AZURE_TENANT_ID", required=False, is_secret=True)
        self.AZURE_CLIENT_ID = self._resolve("AZURE_CLIENT_ID", required=False, is_secret=True)
        self.AZURE_CLIENT_SECRET = self._resolve("AZURE_CLIENT_SECRET", required=False, is_secret=True)

        # Azure OpenAI
        self.AZURE_OPENAI_DEPLOYMENT = self._resolve("AZURE_OPENAI_DEPLOYMENT_NAME")
        self.AZURE_OPENAI_MODEL_NAME = self._resolve("AZURE_OPENAI_MODEL_NAME")
        self.AZURE_OPENAI_API_VERSION = self._resolve("AZURE_OPENAI_API_VERSION")
        self.AZURE_OPENAI_ENDPOINT = self._resolve("AZURE_OPENAI_ENDPOINT")
        self.AZURE_OPENAI_API_KEY = self._resolve("AZURE_OPENAI_API_KEY", required=False, is_secret=True)

        # OpenAI
        self.OPENAI_API_KEY = self._resolve("OPENAI_API_KEY", required=False, is_secret=True)
        self.OPENAI_ENDPOINT = self._resolve("OPENAI_ENDPOINT", required=False)
        self.OPENAI_API_VERSION = self._resolve("OPENAI_API_VERSION", required=False)
        self.OPENAI_MODEL_NAME = self._resolve("OPENAI_MODEL_NAME", required=False)

        # Cosmos
        self.COSMOS_DB_ENDPOINT = self._resolve("COSMOS_DB_ENDPOINT")
        self.COSMOS_DB_KEY = self._resolve("COSMOS_DB_KEY")

        # Other
        self.AZURE_AI_INFERENCE_CHAT_ENDPOINT = self._resolve("AZURE_AI_INFERENCE_CHAT_ENDPOINT")
        self.APPLICATION_INSIGHTS_CONNECTION_STRING = self._resolve(
            "APPLICATIONINSIGHTS_CONNECTION_STRING", required=False, default=""
        )

        # Defaults / business constants
        self.DEFAULT_PROVIDER = self._resolve("DEFAULT_PROVIDER", required=False, default=DEFAULT_PROVIDER_TYPE)
        self.MODELS_WITH_MAX_COMPLETION_TOKENS = MODELS_WITH_MAX_COMPLETION_TOKENS
        self.SECRETS_PATH = self._resolve("AKEYLESS_SECRETS_PATH", required=False, default="/etc/secrets")
        self.MEMORY_PROVIDERS = MEMORY_PROVIDERS
        self.DEFAULT_MEMORY_PROVIDER = DEFAULT_MEMORY_PROVIDER


    def _resolve(
        self,
        name: str,
        required: bool = True,
        default: Optional[str] = None,
        is_secret: bool = False,
    ) -> str:
        """Resolve a config value from environment, secret store, or default.

        Lookup order:
            1. Environment variable (including values loaded from `.env`).
            2. Secret store (only if `is_secret=True`).
            3. Explicit default value (if provided).

        Behavior:
            * If `required=True` and no value can be resolved, raises ValueError.
            * If optional and unresolved, logs a warning and returns an empty string.
            * Environment variables always take precedence over secrets for
            easier local development, even if `is_secret=True`.

        Args:
            name: The environment variable / secret name.
            required: Whether the value must exist. Defaults to True.
            default: Value to use if neither env nor secret is found.
            is_secret: If True, also check the secret store when env is missing.

        Returns:
            str: The resolved value. Never returns None.
        """
        if is_secret:
            value = get_secret(name) or os.getenv(name) or default
        else:
            value = os.getenv(name) or get_secret(name) or default

        if value is None:
            value = default

        if value is None and required:
            raise ValueError(f"Missing required config: {name}")

        if value is None:
            logger.warning("Config %s not found", name)
            value = ""

        return value


# global instance
config = AppConfig()