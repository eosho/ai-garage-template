# client_helper.py

"""
LLM Client Helper Utilities.

This module provides reusable helpers for LLM provider implementations.
It centralizes retry logic, error handling, and usage extraction so that
individual providers remain focused on API-specific details.

Key Features:
    * Retry async client calls with exponential backoff.
    * Extract usage statistics (token counts) from LLM responses.
    * Consistent logging and telemetry integration.

Typical Usage:
    >>> from factory.llm.client_helper import LLMClientHelper
    >>>
    >>> async def call_model():
    ...     return await client.chat.completions.create(
    ...         model="gpt-4o",
    ...         messages=[{"role": "user", "content": "Hello"}]
    ...     )
    >>>
    >>> response = await LLMClientHelper.run_with_retry(call_model)
    >>> usage = LLMClientHelper.extract_usage(response)
    >>> print(response.choices[0].message.content)
    "Hi there!"
    >>> print(usage)
    {'prompt_tokens': 5, 'completion_tokens': 7, 'total_tokens': 12}

Classes:
    LLMClientHelper: Provides retry and usage-extraction utilities.
"""

import asyncio
from typing import Any, Dict

from src.factory.logger.telemetry import telemetry


# Get a logger and tracer
logger = telemetry.get_logger(__name__)
tracer = telemetry.get_tracer(__name__)


class LLMClientHelper:
    """
    Helper class for LLM client operations with retry and usage extraction.

    Example:
        >>> async def call_model():
        ...     return await client.chat.completions.create(...)
        >>> response = await LLMClientHelper.run_with_retry(call_model)
        >>> usage = LLMClientHelper.extract_usage(response)
    """

    @staticmethod
    async def run_with_retry(call_fn, max_attempts: int = 3, delay_base: int = 2) -> Any:
        """Retry wrapper for async LLM calls with exponential backoff.

        Args:
            call_fn: The async function to call.
            max_attempts: Maximum number of attempts.
            delay_base: Base delay in seconds for exponential backoff.

        Returns:
            The result of the call_fn if successful.
        """
        for attempt in range(max_attempts):
            try:
                response = await call_fn()
                return response
            except Exception as e:
                logger.warning(f"Attempt {attempt+1}/{max_attempts} failed: {e}")
                if attempt < max_attempts - 1:
                    wait_time = delay_base**attempt
                    logger.info(f"Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    raise


    @staticmethod
    def extract_usage(response) -> Dict[str, int]:
        """Extract usage tokens if available.

        Args:
            response: The response object from the LLM call.
        """
        if hasattr(response, "usage") and response.usage:
            return {
                "prompt_tokens": getattr(response.usage, "prompt_tokens", 0),
                "completion_tokens": getattr(response.usage, "completion_tokens", 0),
                "total_tokens": getattr(response.usage, "total_tokens", 0),
            }
        return {}
