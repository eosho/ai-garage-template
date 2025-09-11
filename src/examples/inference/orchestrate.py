# orchestrate.py

"""
Agent chain orchestrator.

This script imports HazardIdentificationAgent and HazardPrioritizationAgent
and calls them in sequence:
  1. Identify hazards in an image
  2. Prioritize the hazards
"""

import argparse
import asyncio

from factory.llm.factory import LLMFactory
from hazard_agent.inference.identification_agent import HazardIdentificationAgent
from hazard_agent.inference.prioritization_agent import HazardPrioritizationAgent
from factory.logger.telemetry import LoggingFactory

# Initialize telemetry
logging_factory = LoggingFactory()

logger = logging_factory.get_logger(__name__)
tracer = logging_factory.get_tracer(__name__)



class HazardOrchestrationAgent:
    """Agent wrapper for hazard orchestration using an LLM provider."""

    def __init__(self, provider):
        """
        Initialize the hazard orchestration agent.

        Args:
            provider: An instance of an LLMProviderBase subclass (e.g., AzureInferenceProvider).
        """
        self.provider = provider

    async def orchestrate(self, image_path: str, query: str):
        """Orchestrate hazard identification and prioritization.

        Args:
            image_path (str): Path to the image to analyze.
            query (str): Query to guide the hazard identification agent.
        """
        

        # Step 1: Hazard Identification
        identification_agent = HazardIdentificationAgent(
            provider=self.provider,
        )
        identification_result = await identification_agent.analyze_image(image_path, query)

        logger.info("Hazard Identification Result: %s", identification_result)

        


        # Step 2: Hazard Prioritization
        prioritization_agent = HazardPrioritizationAgent(
            provider=self.provider
        )
        prioritization_result = await prioritization_agent.analyze(str(identification_result))

        logger.info("Hazard Prioritization Result: %s", prioritization_result)

        await self.provider.client.close()

async def main(image_path: str, query: str):
    # Create the provider via factory
    provider = await LLMFactory.create_llm_provider()

    # Pass provider directly into the agent
    agent = HazardOrchestrationAgent(provider=provider)
    await agent.orchestrate(image_path, query)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run hazard identification followed by prioritization."
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
        default="What hazards can you find in this image?",
        help="Query to guide the hazard identification agent."
    )

    args = parser.parse_args()
    asyncio.run(main(args.image, args.query))
