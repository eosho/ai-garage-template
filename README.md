# Factory Module Documentation

The Factory module provides a set of core, reusable components for building AI applications. It is organized into submodules for configuration, logging, LLM interaction, memory management, and prompt engineering. Each submodule is designed to be modular, configurable, and easy to use.

For detailed documentation on each component, please refer to the links below.

## Modules

- **[Agents](./docs/agents.md)**: A framework for creating and managing agents that integrate with the Azure AI Projects SDK.
- **[Config](./docs/config.md)**: A centralized configuration loader using environment variables and `.env` files.
- **[LLM](./docs/llm.md)**: A factory-based system for interacting with various Large Language Models (LLMs) through a unified interface.
- **[Logger](./docs/logger.md)**: A factory for configuring structured logging and distributed tracing using OpenTelemetry.
- **[Memory](./docs/memory.md)**: A standardized way to manage persistent, long-term memory for AI agents.
- **[Prompt](./docs/prompt.md)**: A simple and effective manager for creating and handling prompts from strings or `.prompty` files.
- **[Utils](./docs/utils.md)**: Shared helper functions and utilities used across the factory modules.

---

## Environment Variables

The following environment variables are used to configure the factory modules:

```env
# LLM Provider ('azure-ai-project', 'azure-ai-inference', 'azure_openai')
DEFAULT_PROVIDER_TYPE=azure_openai

# Azure OpenAI / AI Inference Settings
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name
AZURE_OPENAI_MODEL_NAME=your_model_name
AZURE_OPENAI_API_VERSION=2024-06-01
AZURE_AI_INFERENCE_CHAT_ENDPOINT=your_inference_endpoint

# OpenAI Settings
OPENAI_API_KEY=sk-your_key
OPENAI_ENDPOINT=https://api.openai.com/v1
OPENAI_MODEL_NAME=gpt-4o
OPENAI_API_VERSION=v1

# Memory Provider ('cosmosdb', 'json')
DEFAULT_MEMORY_PROVIDER=json

# Cosmos DB Settings
COSMOS_DB_ENDPOINT=your_cosmos_endpoint
COSMOS_DB_KEY=your_cosmos_key

# Telemetry
APPLICATIONINSIGHTS_CONNECTION_STRING=your_app_insights_connection_string
```

