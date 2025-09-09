"""Hazard Prioritization Agent
"""

import asyncio
import json

from prompts.prompts import HAZARD_PRIORITIZATION_PROMPT
from src.factory.llm.factory import LLMFactory
from src.factory.prompt.manager import PromptManager, PromptSourceType
from src.factory.logger.telemetry import LoggingFactory
from src.factory.memory.factory import MemoryFactory
from src.factory.agents.ai_projects.generic_agent import GenericAgent

# Initialize telemetry
logging_factory = LoggingFactory()

# Get a logger and tracer
logger = logging_factory.get_logger(__name__)
tracer = logging_factory.get_tracer(__name__)


class HazardPrioritizationAgent(GenericAgent):
    """Specialized agent for hazard identification."""

    def __init__(self, project_client, *args, **kwargs) -> None:
        super().__init__(project_client=project_client, *args, **kwargs)
        self.project_client = project_client

        # Register hazard identification prompt once at init
        self.prompt_manager = PromptManager()
        self.prompt_manager.register_prompt(
            name="hazard_prioritization_agent_prompt",
            source=HAZARD_PRIORITIZATION_PROMPT,
            source_type=PromptSourceType.STRING,
        )

    def get_instructions(self) -> str:
        """Return hazard prioritization instructions from PromptManager."""
        return self.prompt_manager.hazard_prioritization_agent_prompt()

async def create_agent(query: str = ""):
    """Initialize and run the HazardPrioritizationAgent.

    Args:
        query (str): User query to guide hazard prioritization.
    """
    # Create the provider via factory
    provider = await LLMFactory.create_llm_provider()
    logger.info("Provider type=%s, deployment=%s", provider.provider_type, provider.deployment_name)

    # Initialize memory (if needed)
    memory = MemoryFactory.init(
        memory_store="json",
        file_path="src/hazard_agent/memory/memory.json"
    )

    # Use provider.client (AIProjectClient) with GenericAgent wrapper
    async with provider.client as client:
        agent = HazardPrioritizationAgent(
            project_client=client,   # ✅ use the SDK client, not the wrapper
            model=provider.deployment_name,
            name="hazard_prioritization_agent",
            description="Agent that prioritizes hazards in text, images, or sensor data.",
        )

    if query:
        # Create or get a thread
        thread = await agent.get_thread()
        logger.info("Initialized thread id=%s", thread.id)

        try:
            response = await agent.run(user_message=query, thread=thread)
            logger.info("Hazard Prioritization Response: %s", response)

            # Save response to memory
            await memory.create(thread.id, json.loads(response))
            
            # Retrieve from memory
            await memory.get(thread.id)

        except Exception as e:
            logger.error("Agent run failed: %s", e)
    else:
        # Only create the agent definition
        try:
            created = await agent.create(
                name="hazard_prioritization_agent"
            )
            logger.info("Agent created successfully id: %s", created)
            return created
        except Exception as e:
            logger.error("Agent creation failed: %s", e)


if __name__ == "__main__":
    asyncio.run(create_agent(
        query=("""Prioritize the hazards in a construction site with falling objects, slippery surfaces, and electrical hazards.

        {
  "hazards_detected": true,
  "hazard_count": 2,
  "hazards": [
    {
      "type": "ppe_violation",
      "description": "Hard hat left on the floor, worker not wearing head protection",
      "severity": "high",
      "location": "warehouse floor, near shelving",
      "recommendations": "Ensure workers wear hard hats at all times in warehouse; train staff on PPE compliance"
    },
    {
      "type": "floor_safety",
      "description": "Worker appears to have suffered an injury on the floor",
      "severity": "high",
      "location": "warehouse aisle near shelving",
      "recommendations": "Investigate cause of injury, keep aisles clear, and enforce ladder and equipment safety procedures"
    }
  ]
}""")
    ))
