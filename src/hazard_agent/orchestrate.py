# orchestrator.py
"""
Hazard Orchestrator Agent.

This module coordinates hazard identification and prioritization by connecting
specialized agents via Azure AI Agent Service. It supports:
    - Uploading images
    - Passing multimodal inputs (text + image)
    - Routing to hazard identification and prioritization agents
    - Returning structured JSON responses

Usage:
    python orchestrator.py --image ./hazard.jpg --query "What hazards are present?"
"""

import argparse
import asyncio
import json

from azure.ai.agents.models import (
    ConnectedAgentDetails,
    ConnectedAgentToolDefinition,
    MessageImageFileParam,
    MessageInputTextBlock,
    MessageInputImageFileBlock,
)
from azure.core.exceptions import AzureError

from prompts.prompts import HAZARD_ORCHESTRATOR_PROMPT
from src.factory.llm.factory import LLMFactory
from src.factory.prompt.manager import PromptManager, PromptSourceType
from src.factory.logger.telemetry import LoggingFactory
from src.factory.agents.ai_projects.generic_agent import GenericAgent



# Initialize telemetry
logging_factory = LoggingFactory()

# Get a logger and tracer
logger = logging_factory.get_logger(__name__)
tracer = logging_factory.get_tracer(__name__)


def get_identification_tool(agent_id: str) -> ConnectedAgentToolDefinition:
    """Build the ConnectedAgentToolDefinition for the Hazard Identification Agent.

    Args:
        agent_id (str): The ID of the hazard identification agent.

    Returns:
        ConnectedAgentToolDefinition: Configured tool definition for orchestration.
    """
    return ConnectedAgentToolDefinition(
        connected_agent=ConnectedAgentDetails(
            id=agent_id,
            name="hazard_identification_agent",
            description="Analyzes text and images to detect hazards such as PPE violations, spills, or obstructions.",
        )
    )


def get_prioritization_tool(agent_id: str) -> ConnectedAgentToolDefinition:
    """Build the ConnectedAgentToolDefinition for the Hazard Prioritization Agent.

    Args:
        agent_id (str): The ID of the hazard prioritization agent.

    Returns:
        ConnectedAgentToolDefinition: Configured tool definition for orchestration.
    """
    return ConnectedAgentToolDefinition(
        connected_agent=ConnectedAgentDetails(
            id=agent_id,
            name="hazard_prioritization_agent",
            description="Assigns priority levels to identified hazards based on severity, risk, and safety context.",
        )
    )


class HazardOrchestrationAgent(GenericAgent):
    """Specialized agent for orchestrating hazard-related workflows."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        # Register orchestration prompt once
        self.prompt_manager = PromptManager()
        self.prompt_manager.register_prompt(
            name="hazard_orchestration_agent_prompt",
            source=HAZARD_ORCHESTRATOR_PROMPT,
            source_type=PromptSourceType.STRING,
        )

    def get_instructions(self) -> str:
        """Return orchestration instructions from PromptManager."""
        return self.prompt_manager.hazard_orchestration_agent_prompt()


async def orchestrator(query: str, image_path: str) -> None:
    """Initialize and run the Hazard Orchestration Agent.

    Args:
        query (str): User query to guide hazard identification.
        image_path (str): Path to the image to analyze.
    """
    with tracer.start_as_current_span("orchestrate_hazard_agents"):
        logger.info("Starting hazard orchestration workflow.")

        # Build connected tools
        identification_tool = get_identification_tool("asst_2kJpvyzwdBXdav0kSunl8exQ")
        prioritization_tool = get_prioritization_tool("asst_1wUZWO4Eg6UTvttUO1inB49W")

        # LLM Provider
        provider = await LLMFactory.create_llm_provider()
        logger.info("Provider type=%s, deployment=%s", provider.provider_type, provider.deployment_name)

        async with provider.client as client:
            agent = HazardOrchestrationAgent(
                project_client=client,
                model=provider.deployment_name,
                name="hazard_orchestrator",
                description="Coordinates hazard identification and prioritization.",
                tools=[identification_tool, prioritization_tool],
            )

            # Upload image
            file_id = await agent.upload_file(image_path)
            if not file_id:
                logger.error("No files uploaded. Exiting workflow.")
                return
            logger.info("Uploaded file IDs: %s", file_id)

            # Create or get a thread
            thread = await agent.get_thread()
            logger.info("Thread initialized id=%s", thread.id)

            # Input blocks
            file_param = MessageImageFileParam(file_id=file_id, detail="high")
            content_blocks = [
                MessageInputTextBlock(text=query),
                MessageInputImageFileBlock(image_file=file_param),
            ]

            try:
                response = await agent.run(content_blocks, thread)

                # Pretty-print validated JSON if possible
                try:
                    parsed = json.loads(response) if isinstance(response, str) else response
                    logger.info("Hazard Agent Response:\n%s", json.dumps(parsed, indent=2))

                    # Clean up & delete the uploaded files
                    if file_id:
                        await agent.delete_uploaded_file(file_id)

                    await agent.project_client.close()
                except json.JSONDecodeError:
                    logger.warning("Response not valid JSON. Raw: %s", response)

            except AzureError as e:
                logger.error("AzureError during orchestration: %s", e)
            except Exception as e:
                logger.error("Unexpected failure: %s", e)


# ---------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run hazard orchestration agent workflow."
    )
    parser.add_argument(
        "--image",
        type=str,
        default="src/hazard_agent/images/hazard.jpg",
        help="Path to the image to analyze."
    )
    parser.add_argument(
        "--query",
        type=str,
        default="Analyze the base64 image and identify hazards in the image?",
        help="Text query to guide the hazard identification agent."
    )
    args = parser.parse_args()

    asyncio.run(orchestrator(args.query, args.image))
