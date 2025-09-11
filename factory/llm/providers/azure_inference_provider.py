# azure_inference_provider.py

"""
Azure AI Inference Provider (Generic Adapter).

This module defines the provider implementation for Azure AI Inference-based
chat completions. It keeps the consumer API generic (dicts, lists, callables)
while internally adapting to Azure's typed message and tool models.

Features:
    * Accepts user/system prompts as plain strings or multimodal dicts.
    * Accepts Python functions as tools (auto-converts to Azure tool definitions).
    * Handles tool calls by executing registered Python callables.
    * Supports structured outputs (JSON schema, response_format).
    * Returns simple str or (str, usage) so consumers never import Azure SDK models.

Example (generic app code, no Azure imports):
    >>> response, usage = await provider.get_completion(
    ...     system_prompt="Detect hazards in this image.",
    ...     user_prompt=[
    ...         {"type": "text", "text": "What hazards do you see?"},
    ...         {"type": "image_url", "url": "https://example.com/hazard.jpg"},
    ...     ],
    ...     tools=[get_current_datetime],
    ...     return_usage=True,
    ... )
    >>> print(response)
    {"hazards": ["ladder", "spill"]}
"""

import json
from typing import Any, Dict, Tuple, Union, Callable, List

from azure.ai.inference.models import (
    SystemMessage,
    UserMessage,
    ToolMessage,
    ChatCompletionsToolDefinition,
    FunctionDefinition,
    ChatCompletionsToolCall,
    ChatRequestMessage,
    TextContentItem,
    ImageContentItem,
    ImageUrl,
    ImageDetailLevel
)
from .base_provider import LLMProviderBase
from ..client_helper import LLMClientHelper
from factory.llm.llm_model_config import LLMModelConfig
from factory.logger.telemetry import telemetry


# Get a logger and tracer
logger = telemetry.get_logger(__name__)
tracer = telemetry.get_tracer(__name__)


class AzureInferenceProvider(LLMProviderBase):
    """Generic adapter provider for Azure AI Inference (chat + completion)."""

    def __init__(self, client: Any, model_config: LLMModelConfig):
        super().__init__(model_config, "azure-ai-inference")
        self.client = client
        self.model_config = model_config
        self.tool_registry: Dict[str, Callable[..., str]] = {}

    def register_tool(self, func: Callable[..., str]) -> ChatCompletionsToolDefinition:
        """
        Register a Python function as a tool callable by the model.

        Args:
            func (Callable[..., str]): Function with a name + docstring.

        Returns:
            ChatCompletionsToolDefinition: The corresponding tool schema.
        """
        tool_def = ChatCompletionsToolDefinition(
            function=FunctionDefinition(
                name=func.__name__,
                description=func.__doc__ or "No description provided.",
                parameters={"type": "object", "properties": {}},  # can introspect signature later
            )
        )
        self.tool_registry[func.__name__] = func
        logger.info("Registered tool '%s' for model=%s", func.__name__, self.model_config.name)
        return tool_def

    async def _handle_tool_calls(
        self,
        messages: list,
        tool_calls: list,
    ) -> str:
        """
        Handle tool calls returned by the model.

        Args:
            messages (list): Current conversation messages (System/User/Tool).
            tool_calls (list): Tool calls returned by the model.

        Returns:
            str: Result of the first executed tool call (if any).
        """
        for tool_call in tool_calls:
            if not isinstance(tool_call, ChatCompletionsToolCall):
                continue

            args = json.loads(tool_call.function.arguments or "{}")
            func = self.tool_registry.get(tool_call.function.name)

            if not func:
                logger.warning("No registered tool found for '%s'", tool_call.function.name)
                continue

            try:
                result = func(**args)
                logger.info(
                    "Executed tool '%s' with args=%s result=%s",
                    tool_call.function.name, args, result
                )

                messages.append(
                    ToolMessage(content=result, tool_call_id=tool_call.id)
                )

                return result
            except Exception as e:
                logger.error(
                    "Error executing tool '%s' with args=%s: %s",
                    tool_call.function.name, args, e, exc_info=True
                )
                raise

        return ""

    async def get_completion(
        self,
        system_prompt: str,
        user_prompt: Union[str, List[Dict[str, Any]]],
        **kwargs: Any,
    ) -> Union[str, Tuple[str, Dict[str, Any]]]:
        """
        Generate a completion using system and user prompts.

        Args:
            system_prompt (str): System context message.
            user_prompt (Union[str, List[Dict]]): User input; plain string or multimodal blocks.
            **kwargs (Any): Optional runtime args:
                - tools (list[Callable]): Python functions to expose as tools.
                - tool_choice (str): Tool selection mode ("auto", "none", etc.).
                - response_format (Any): Structured output schema.
                - return_usage (bool): If True, return (content, usage).

        Returns:
            str or (str, Dict): Response text, optionally with usage metadata.
        """
        # Build messages
        messages: list[ChatRequestMessage] = [
            SystemMessage(content=system_prompt)
        ]
        if isinstance(user_prompt, str):
            # Wrap plain text in a TextContentItem
            messages.append(UserMessage(content=[TextContentItem(text=user_prompt)]))

        elif isinstance(user_prompt, list):
            content_items = []
            for block in user_prompt:
                if block["type"] == "text":
                    content_items.append(TextContentItem(text=block["text"]))
                elif block["type"] == "image_url":
                    content_items.append(
                        ImageContentItem(
                            image_url=ImageUrl(
                                url=block["image_url"]["url"],
                                detail=ImageDetailLevel.HIGH
                            )
                        )
                    )
            messages.append(UserMessage(content=content_items))
        else:
            raise TypeError("user_prompt must be str or list[dict]")

        # Register and adapt tools
        tool_defs = []
        for func in kwargs.get("tools", []):
            tool_defs.append(self.register_tool(func))

        # Build request payload (filtering unsupported args)
        request_payload = self.model_config.build_request_args(**kwargs)
        request_payload.update({
            "model": self.model_config.name,
            "messages": messages,
        })
        if tool_defs:
            request_payload["tools"] = tool_defs
        if "tool_choice" in kwargs:
            request_payload["tool_choice"] = kwargs["tool_choice"]

        logger.debug("Final request payload=%s", request_payload)

        async def _call():
            return await self.client.complete(**request_payload)

        response = await LLMClientHelper.run_with_retry(_call)
        if not response or not response.choices:
            raise ValueError("No response received from Azure AI Inference")

        choice = response.choices[0].message

        # Handle tool calls
        if getattr(choice, "tool_calls", None):
            return await self._handle_tool_calls(messages, choice.tool_calls)

        content = (choice.content or "").strip()

        if kwargs.get("return_usage"):
            return content, LLMClientHelper.extract_usage(response)

        return content
