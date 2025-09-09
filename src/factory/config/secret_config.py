# secrets_utils.py

"""
Secrets Utility Module.

Provides helper functions for managing secrets stored on the filesystem
(e.g., under `/etc/secrets` in containers or a configured local path).
Secrets are expected to be stored as `.txt` files, each containing a single value.

Features:
    * Fetch individual secrets by filename (`get_secret`).
    * List all available secrets in the configured directory (`list_secrets`).
    * Check existence of specific secrets (`secret_exists`).
    * Automatic support for filenames with or without `.txt` extension.
    * Graceful handling of missing or unreadable secrets (returns None).

Constants:
    SECRETS_PATH (str): Path to the secrets directory, defaulting to
        `AKEYLESS_SECRETS_PATH` from `.constants`.

Functions:
    get_secret(filename: str) -> Optional[str]:
        Retrieve the content of a secret file.
    list_secrets() -> list[str]:
        List all `.txt` files in the secrets directory.
    secret_exists(filename: str) -> bool:
        Check whether a given secret file exists.

Usage:
    >>> from factory.secrets.utils import get_secret, list_secrets, secret_exists
    >>> cosmos_uri = get_secret("azure.cosmos.uri")
    >>> print(cosmos_uri)
    "AccountEndpoint=https://example.documents.azure.com:443/;AccountKey=..."

    >>> available = list_secrets()
    >>> print(available)
    ["azure.cosmos.uri.txt", "azure.openai.key.txt"]

    >>> exists = secret_exists("azure.openai.key")
    >>> print(exists)
    True

Environment:
    By default, the secrets path is set from `AKEYLESS_SECRETS_PATH`. This should
    typically point to `/etc/secrets` in a Kubernetes/Docker environment, or a
    simulated directory on local development machines (e.g., `./secrets`).
"""

from pathlib import Path
from typing import Optional

from .constants import AKEYLESS_SECRETS_PATH
from src.factory.logger.telemetry import LoggingFactory

# Initialize telemetry (Azure Monitor if configured, otherwise fallback to console)
logging_factory = LoggingFactory()
logger = logging_factory.get_logger(__name__)

# Default secrets directory
SECRETS_PATH = AKEYLESS_SECRETS_PATH


def _resolve_secret_path(filename: str) -> Path:
    """Return the full path to a secret file, adding `.txt` if missing."""
    if not filename.endswith(".txt"):
        filename = f"{filename}.txt"
    return Path(SECRETS_PATH) / filename


def get_secret(filename: str) -> Optional[str]:
    """
    Fetch a secret value from the configured secrets path.

    Args:
        filename: Secret name (with or without `.txt` extension).

    Returns:
        Secret value as a string, or None if not found or unreadable.
    """
    secret_path = _resolve_secret_path(filename)

    try:
        if not secret_path.exists():
            return None

        secret = secret_path.read_text(encoding="utf-8").strip()
        return secret or None
    except Exception as e:
        logger.error("Error reading secret '%s': %s", filename, e)
        return None


def list_secrets() -> list[str]:
    """
    List all available secrets in the secrets directory.

    Returns:
        List of `.txt` filenames, or an empty list if directory is missing/unreadable.
    """
    try:
        secrets_dir = Path(SECRETS_PATH)
        if not secrets_dir.exists():
            return []
        return [f.name for f in secrets_dir.glob("*.txt")]
    except Exception as e:
        logger.error("Error listing secrets: %s", e)
        return []


def secret_exists(filename: str) -> bool:
    """
    Check if a secret file exists.

    Args:
        filename: Secret name (with or without `.txt` extension).

    Returns:
        True if the file exists, False otherwise.
    """
    return _resolve_secret_path(filename).exists()
