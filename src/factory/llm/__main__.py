"""Main script to test LLMFactory and provider creation."""

import asyncio
from .factory import LLMFactory
import asyncio
from ..logger.telemetry import (
    LoggingFactory,
    TelemetryLevel,
    TracingProvider
)

# Initialize telemetry (console for local dev)
logging_factory = LoggingFactory(
    default_level=TelemetryLevel.INFO,
    tracing_provider=TracingProvider.AZURE_MONITOR
)
logger = logging_factory.get_logger(__name__)
tracer = logging_factory.get_tracer(__name__)

async def main():
    with tracer.start_as_current_span("test_llm_request"):
        llm_factory = LLMFactory()

        # Create provider using the factory
        provider = await llm_factory.create_llm_provider(llm_factory.get_model_config())

        if provider.client:
            logger.info(f"Provider type: {provider.provider_type}")
            logger.info(f"Deployment: {provider.deployment_name}")

            # Use the provider for inference
            response = await provider.get_completion(
                system_prompt="You are a helpful assistant that specializes in math. Make sure to always explain your answer to the user",
                user_prompt="What is the integral of x^2?",
                max_tokens=1000,
                return_usage=True
            )
            logger.info(f"Chat response: \n{response}")

if __name__ == "__main__":
    asyncio.run(main())
