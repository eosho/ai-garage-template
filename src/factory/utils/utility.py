from typing import Callable, Dict, Any, Set
from azure.identity import (
  DefaultAzureCredential,
  AzureDeveloperCliCredential,
  ClientSecretCredential
)
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import ClientAuthenticationError

from src.factory.config.app_config import config
from src.factory.logger.telemetry import LoggingFactory

# Initialize telemetry
logging_factory = LoggingFactory()

# Get a logger and tracer
logger = logging_factory.get_logger(__name__)
tracer = logging_factory.get_tracer(__name__)


def _get_azure_credential(api_key: str = "") -> Any:
    """
    Resolve Azure credential chain.

    Tries multiple authentication methods in order:
    1. ClientSecretCredential
    2. DefaultAzureCredential
    3. AzureDeveloperCliCredential
    4. AzureKeyCredential (if api_key is provided)

    Args:
        api_key (str): The API key to use for AzureKeyCredential.

    Returns:
        Credential instance usable for Azure SDK clients.

    Raises:
        ClientAuthenticationError: If no credential can be created.
    """
    if api_key:
        logger.info("Using AzureKeyCredential (from API key)")
        return AzureKeyCredential(api_key)

    credential_attempts = [
        ("ClientSecretCredential", lambda: ClientSecretCredential(
            tenant_id=config.AZURE_TENANT_ID,
            client_id=config.AZURE_CLIENT_ID,
            client_secret=config.AZURE_CLIENT_SECRET,
        )),
        ("DefaultAzureCredential", lambda: DefaultAzureCredential()),
        ("AzureDeveloperCliCredential", lambda: AzureDeveloperCliCredential(
            tenant_id=config.AZURE_TENANT_ID
        )),
    ]

    for name, factory in credential_attempts:
        try:
            cred = factory()
            logger.info("Using %s", name)
            return cred
        except Exception as e:
            logger.warning("%s initialization failed: %s", name, e)

    msg = "All credential methods failed."
    logger.error(msg)
    raise ClientAuthenticationError(msg)



# Statically defined utility functions for fast reference
utility_functions: Set[Callable[..., Any]] = {
    _get_azure_credential,
}