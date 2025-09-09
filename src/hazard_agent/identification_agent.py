"""
Hazard Identification Agent Module.

This module defines a specialized agent for hazard identification, extending
GenericAgent. It wires in domain-specific prompts via PromptManager and shows
how to initialize and run the agent with a provider created by LLMFactory.

Features:
    - Uses PromptManager to manage hazard-specific prompts.
    - Async lifecycle management of Azure AI Project / Inference clients.
    - Structured logging of provider type, deployment, and thread IDs.
    - Extendable for multi-turn conversations with optional persistence.
    - Supports multimodal input (text + images).

Usage:
    $ python -m src.agents.identification_agent
"""

import asyncio
from azure.ai.agents.models import (
    MessageImageFileParam,
    MessageInputTextBlock,
    MessageInputImageFileBlock,
)

from prompts.prompts import HAZARD_IDENTIFICATION_PROMPT
from src.factory.llm.factory import LLMFactory
from src.factory.prompt.manager import PromptManager, PromptSourceType
from src.factory.logger.telemetry import LoggingFactory
from src.factory.agents.ai_projects.generic_agent import GenericAgent


# Initialize telemetry
logging_factory = LoggingFactory()

# Get a logger and tracer
logger = logging_factory.get_logger(__name__)
tracer = logging_factory.get_tracer(__name__)


class HazardIdentificationAgent(GenericAgent):
    """Specialized agent for hazard identification."""

    def __init__(self, project_client, *args, **kwargs) -> None:
        super().__init__(project_client=project_client, *args, **kwargs)
        self.project_client = project_client

        # Register hazard identification prompt once at init
        self.prompt_manager = PromptManager()
        self.prompt_manager.register_prompt(
            name="hazard_identification_agent_prompt",
            source=HAZARD_IDENTIFICATION_PROMPT,
            source_type=PromptSourceType.STRING,
        )

    def get_instructions(self) -> str:
        """Return hazard identification instructions from PromptManager."""
        return self.prompt_manager.hazard_identification_agent_prompt()

async def create_agent(image_path: str = "", query: str = ""):
    """Analyze an image + query for hazard identification.

    Args:
        image_path (str): Path to the image file to upload.
        query (str): User query to guide hazard identification.
    """
    # Create the provider via factory
    provider = await LLMFactory.create_llm_provider()
    logger.info("Provider type=%s, deployment=%s", provider.provider_type, provider.deployment_name)

    # Use provider.client (AIProjectClient) with GenericAgent wrapper
    async with provider.client as client:
        agent = HazardIdentificationAgent(
            project_client=client,   # ✅ use the SDK client, not the wrapper
            model=provider.deployment_name,
            name="hazard_identification_agent",
            description="Agent that identifies hazards in text, images, or sensor data.",
        )
    # Create or get a thread
    thread = await agent.get_thread()
    logger.info("Initialized thread id=%s", thread.id)

    # Upload image
    uploaded_ids = await agent.upload_file(image_path)
    logger.info("Uploaded file IDs: %s", uploaded_ids)

    # Prepare multimodal content blocks
    file_param = MessageImageFileParam(file_id=uploaded_ids, detail="auto")
    content_blocks = [
        MessageInputTextBlock(text=query),
        MessageInputImageFileBlock(image_file=file_param),
    ]

    if image_path and query:
        # Create or get a thread
        thread = await agent.get_thread()
        logger.info("Initialized thread id=%s", thread.id)

        try:
            response = await agent.run(user_message=content_blocks, thread=thread)
            logger.info("Hazard Identification Response: %s", response)

        except Exception as e:
            logger.error("Agent run failed: %s", e)
    else:
        # Only create the agent definition
        try:
            created = await agent.create(
                name="hazard_identification_agent"
            )
            logger.info("Agent created successfully id: %s", created)
            return created
        except Exception as e:
            logger.error("Agent creation failed: %s", e)
            raise


if __name__ == "__main__":
    asyncio.run(create_agent(
        image_path="src/hazard_agent/images/hazard.jpg",
        query="Analyze the base64 image and identify hazards in the image?",
    ))
