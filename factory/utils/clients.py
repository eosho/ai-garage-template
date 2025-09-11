import json

from typing import Callable, Any, Set
from azure.identity import (
  DefaultAzureCredential,
  AzureDeveloperCliCredential,
  ClientSecretCredential
)
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import ClientAuthenticationError
from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError
from google.oauth2 import service_account

from factory.config.app_config import config
from factory.logger.telemetry import telemetry

# Get a logger and tracer
logger = telemetry.get_logger(__name__)
tracer = telemetry.get_tracer(__name__)


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


def _get_bigquery_client(
        project_id: str = "",
        location: str = "",
    ) -> Any:
        """
        Initialize the BigQuery manager.

        Authentication is resolved automatically in the following order:
            1. BQ_CREDENTIALS_FILE → Path to a service account JSON key file.
            2. BQ_CREDENTIALS_JSON → JSON string or dict of service account credentials.
            3. Application Default Credentials (ADC) → Falls back if neither is set.

        Configuration values are sourced from app_config.py.

        Args:
            project_id (str): Optional. Google Cloud project ID.
            location (str): Optional. Default dataset location.

        Raises:
            BigQueryError: If the client cannot be initialized.
        """

        try:
            credentials = None

            # Check if Big query credential file or json was provided.
            if config.BQ_CREDENTIALS_FILE:
                # Load credentials from file
                credentials = service_account.Credentials.from_service_account_file(
                    config.BQ_CREDENTIALS_FILE
                )
                logger.debug("Loaded BigQuery credentials from file: %s", config.BQ_CREDENTIALS_FILE)

            elif config.BQ_CREDENTIALS_JSON:
                # Parse credentials from JSON string or dict
                credentials_json = config.BQ_CREDENTIALS_JSON
                if isinstance(credentials_json, str):
                    credentials_json = json.loads(credentials_json)
                credentials = service_account.Credentials.from_service_account_info(
                    credentials_json
                )
                logger.debug("Loaded BigQuery credentials from JSON config")

            else:
                logger.debug("No BQ credentials provided in config, using ADC")

            # Instantiate client
            client = bigquery.Client(
                project=project_id,
                location=location,
                credentials=credentials,
            )
            logger.info(
                "Initialized BigQuery client project=%s location=%s", project_id, location
            )
            return client

        except Exception as exc:
            logger.error(
                "Failed to initialize BigQuery client: %s", exc, exc_info=True
            )
            raise Exception("Client initialization failed") from exc


# Statically defined utility functions for fast reference
utility_functions: Set[Callable[..., Any]] = {
    _get_azure_credential,
    _get_bigquery_client
}