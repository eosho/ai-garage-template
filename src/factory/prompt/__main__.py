"""
Prompt Manager Runner.

This utility script demonstrates registering, rendering, listing,
and reloading prompts using the PromptManager.

Run with:
    python -m factory.prompts
"""

import sys
import logging
from pathlib import Path

from .manager import PromptManager, PromptSourceType

from factory.logger.telemetry import (
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


def main():
    # --- Register prompts ---
    PromptManager.register_prompt(
        "greet",
        "Hello {{ name }}!",
        PromptSourceType.STRING,
        #namespace="demo"
    )

    # Optionally: from a file (if `example_prompt.jinja2` exists in same folder)
    jinja_file = Path(__file__).parent / "example_prompt.jinja2"
    if jinja_file.exists():
        PromptManager.register_prompt(
            "incident",
            jinja_file,
            PromptSourceType.JINJA2,
            #namespace="demo"
        )

    # --- Use prompts ---
    pm = PromptManager()

    # Inline string usage
    # print(pm.greet(name="Alice", namespace="demo"))
    print(pm.greet(name="Alice"))

    # Jinja2 template usage
    try:
        print(pm.incident(severity="Critical", service="DB", details="Connection pool exhausted"))
    except Exception as e:
        logging.error("Failed to render incident prompt: %s", e)

    # List registered
    print("Registered prompts:", PromptManager.list_prompts())


if __name__ == "__main__":
    main()
