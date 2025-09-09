# openai_provider.py
from typing import Any

from src.factory.logger.telemetry import LoggingFactory
from ..base_provider import LLMProviderBase
from ..client_helper import LLMClientHelper

logging_factory = LoggingFactory()
logger = logging_factory.get_logger(__name__)

class OpenAIProvider(LLMProviderBase):
    """LLM provider for OpenAI API."""

    def __init__(self, client: Any, deployment_name: str):
        super().__init__(deployment_name, "azure_openai")
        self.client = client

    async def get_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        **kwargs: Any,
    ) -> Any:
        """
        Generate a completion using system and user prompts.

        Args:
            system_prompt (str): System context message for the model.
            user_prompt (str): User input message, which can be plain text
                               or a multimodal payload (e.g., text + image).
            **kwargs (Any): Optional provider-specific parameters, including:
                - max_tokens (int, optional): Maximum number of tokens for the response.
                - response_format (Any, optional): Structured response format
                  (e.g., JSON schema) if supported by the provider.
                - tools (list[dict], optional): Tool/function definitions for
                  function calling.
                - return_usage (bool, optional): If True, return a tuple
                  of (output, usage stats).

        Returns:
            Any:
                - str: Model output as plain text.
                - dict: Tool-call payload if tool calling is used.
                - tuple: (output, usage) if return_usage=True.
        """
        
        params = {
            "temperature": 0.7,
            "model": self.deployment_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        }

        if kwargs.get("response_format") is not None:
            params["response_format"] = kwargs["response_format"]

        if kwargs.get("tools") is not None:
            params["tools"] = kwargs["tools"]

        async def _call():
            return await self.client.chat.completions.create(**params)

        response = await LLMClientHelper.run_with_retry(_call)
        content = response.choices[0].message.content.strip()

        if kwargs.get("return_usage"):
            return content, LLMClientHelper.extract_usage(response)
        return content