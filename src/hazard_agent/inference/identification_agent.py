"""Hazard Identification Agent
"""

import asyncio
import json
import argparse

from typing import Dict, Any
from azure.ai.inference.aio import ChatCompletionsClient
from azure.ai.inference.models import (
    ImageUrl,
    ImageDetailLevel,
    JsonSchemaFormat,
)

from src.hazard_agent.schemas import HazardIdentificationOutput
from src.factory.llm.factory import LLMFactory
from src.hazard_agent.prompts.prompts import HAZARD_IDENTIFICATION_PROMPT
from src.factory.logger.telemetry import LoggingFactory

# Initialize telemetry (Azure Monitor if configured, otherwise fallback to console)
logging_factory = LoggingFactory()

# Get a logger and tracer
logger = logging_factory.get_logger(__name__)
tracer = logging_factory.get_tracer(__name__)


class HazardIdentificationAgent:
    """Agent wrapper for hazard prioritization using an LLM provider."""

    def __init__(self, provider):
        """
        Initialize the hazard prioritization agent.

        Args:
            provider: An instance of an LLMProviderBase subclass (e.g., AzureInferenceProvider).
        """
        self.provider = provider

    @staticmethod
    def get_schema() -> Dict[str, Any]:
        """Return the strict JSON schema for hazard identification."""
        return HazardIdentificationOutput.model_json_schema()

    async def analyze_image(self, image_path: str, query: str) -> str:
        """
        Analyze an image with the hazard identification schema.

        Args:
            image_path (str): Path to the image file.
            query (str): User query to guide hazard analysis.

        Returns:
            str: Strict JSON response containing hazard analysis.
        """
        logger.info("Submitting hazard identification request for image=%s", image_path)

        response = await self.provider.get_completion(
            system_prompt=HAZARD_IDENTIFICATION_PROMPT,
            user_prompt=[
                {
                    "type": "text",
                    "text": query,
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": ImageUrl.load(
                            image_file=image_path,
                            image_format=image_path.split(".")[-1],
                            detail=ImageDetailLevel.HIGH,
                        ).url,
                        "detail": "high",
                    },
                },
            ],
            response_format=JsonSchemaFormat(
                name="hazard_identification_schema",
                schema=self.get_schema(),
                description="Schema for identifying hazards in an image",
                strict=True,
            ),
            max_tokens=1024,
            return_usage=True,
        )

        logger.info("Hazard identification completed.")
        json_str, usage = response

        # Parse the JSON string
        parsed = json.dumps(json.loads(json_str), indent=2)
        logger.debug("Parsed response: %s", parsed)

        # Only if return_usage=True
        logger.info("Token usage: %s", json.dumps(usage, indent=2))

        return parsed


async def main(image_path: str, query: str):
    # Create the provider via factory
    provider = await LLMFactory.create_llm_provider()

    # Pass provider directly into the agent
    agent = HazardIdentificationAgent(provider=provider)
    output = await agent.analyze_image(image_path, query)

    print("=== Hazard Detection Result ===")
    print(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run hazard identification analysis on an image."
    )
    parser.add_argument(
        "--image",
        type=str,
        default="src/hazard_agent/images/hazard.jpg",
        help="Path to the hazard image to analyze."
    )
    parser.add_argument(
        "--query",
        type=str,
        default="What hazards can you find in this image?",
        help="The analysis query to pass alongside the image."
    )
    args = parser.parse_args()

    asyncio.run(main(args.image, args.query))