# Factory Module Documentation

The Factory module provides a set of core, reusable components for building AI applications. It is organized into submodules for configuration, logging, LLM interaction, memory management, and prompt engineering.

## Directory Structure

```
factory/
├── agents/
│   ├── ai_projects/            # Agents for Azure AI Projects
│   │   ├── base_agent.py
│   │   └── generic_agent.py
│   └── langchain/              # (Placeholder for LangChain agents)
├── config/                     # Centralized configuration management
├── llm/                        # Language Model (LLM) provider integration
├── logger/                     # Logging and OpenTelemetry integration
├── memory/                     # Long-term memory providers (Cosmos DB, JSON)
├── prompt/                     # Prompt management and templating
└── utils/                      # Shared utility functions
```

---

## 1. Config Module

Provides a centralized configuration loader using environment variables and `.env` files, with support for secret stores.

#### Key Components:
- `app_config.py`: Main configuration class (`AppConfig`) that loads and provides access to all settings.
- `secret_config.py`: Helper for fetching secrets from a secure location (e.g., Akeyless, Azure Key Vault).

#### Usage Example:
```python
from factory.config.app_config import config

# Access configuration properties
openai_key = config.OPENAI_API_KEY
cosmos_endpoint = config.COSMOS_DB_ENDPOINT

# Check optional settings
if config.APPLICATION_INSIGHTS_CONNECTION_STRING:
    print("Application Insights is configured.")
```

---

## 2. LLM Module

A factory-based module for interacting with various Large Language Models (LLMs) through a unified interface.

#### Key Features:
- **Unified Interface**: `LLMProviderBase` defines a common interface for getting completions.
- **Multi-Provider Support**: Includes providers for `Azure AI Inference`, `Azure AI Projects`, and `OpenAI`.
- **Factory-Based Creation**: `LLMFactory` automatically creates and configures the correct provider based on environment settings.

#### Usage Example:
```python
from factory.llm.factory import LLMFactory

# Create the configured LLM provider
provider = await LLMFactory.create_llm_provider()

# Use the provider to get a completion
response = await provider.completion(
    prompt="You are a helpful assistant. Explain the theory of relativity.",
    max_tokens=100
)
print(response)
```

---

## 3. Logger Module

Configures structured logging and distributed tracing using OpenTelemetry, with built-in support for Azure Monitor.

#### Key Features:
- **`LoggingFactory`**: A singleton factory to configure and provide `logger` and `tracer` instances.
- **Multiple Backends**: Supports `Azure Monitor` for production and a simple `Console` exporter for local development.
- **Standardized Levels**: Uses a `TelemetryLevel` enum for consistent log level configuration.

#### Usage Example:
```python
from factory.logger.telemetry import LoggingFactory, TelemetryLevel

# Configure logging at application startup
LoggingFactory.configure(default_level=TelemetryLevel.INFO)

# Get a logger instance
logger = LoggingFactory.get_logger(__name__)
logger.info("This is an informational message.")
logger.warning("This is a warning.")

# Get a tracer for distributed tracing
tracer = LoggingFactory.get_tracer(__name__)
with tracer.start_as_current_span("my-operation"):
    # Your code here
    logger.info("Doing work inside a trace span.")
```

---

## 4. Memory Module

Provides a generic interface for persistent, long-term memory storage, allowing agents to maintain state across sessions.

#### Key Features:
- **`MemoryProviderBase`**: An abstract base class defining the `save` and `load` interface.
- **Multi-Backend Support**: Includes providers for `Cosmos DB` and local `JSON` files.
- **`MemoryFactory`**: Creates the appropriate memory provider based on configuration.

#### Usage Example:
```python
from factory.memory.factory import MemoryFactory
from factory.config.constants import DEFAULT_MEMORY_PROVIDER

# Create the default memory provider
memory_provider = MemoryFactory().init(memory_store=DEFAULT_MEMORY_PROVIDER)

# Save state for a session
session_id = "user_123"
state_data = {"history": ["Hello"], "context": "conversation about weather"}
await memory_provider.save(session_id, state_data)

# Load state for the same session
loaded_data = await memory_provider.load(session_id)
print(loaded_data)
```

---

## 5. Prompt Module

A simple and effective manager for creating and handling prompts from strings or `.prompty` files.

#### Key Features:
- **`PromptManager`**: A class to create, cache, and render prompts.
- **Multiple Sources**: Supports creating prompts from inline strings or loading from `.prompty` files.
- **Simple Templating**: Uses standard `{{variable}}` syntax for substitutions.
- **Error Handling**: Custom exceptions for `PromptNotFound` and `PromptRenderError`.

#### Usage Example:
```python
from factory.prompt.prompt import PromptManager, create_simple_prompt

# Initialize the manager
prompt_manager = PromptManager()

# 1. Use a utility function to create a prompt string
prompt_str = create_simple_prompt(
    system_message="You are a helpful assistant.",
    user_message="Translate '{{text_to_translate}}' to {{language}}."
)

# 2. Generate messages by substituting variables
messages = prompt_manager.create_and_generate(
    prompt_str,
    text_to_translate="Hello, world!",
    language="Spanish"
)
print(messages)

# 3. Load a prompt from a .prompty file
try:
    messages_from_file = prompt_manager.load_and_generate(
        "path/to/your/prompt.prompty",
        variable1="value1"
    )
    print(messages_from_file)
except FileNotFoundError as e:
    print(e)
```

---

## 6. Utils Module

Contains shared helper functions used across the factory modules.

- **`utility.py`**: Includes functions like `_get_azure_credential()` to simplify obtaining credentials for Azure services.

---

## 7. AI Projects Agents

This submodule contains agents designed to work with the Azure AI Projects SDK.

#### Key Components:

*   **`base_agent.py`**: Defines the `BaseAgent` abstract base class. This class establishes a common interface for all Azure AI Project agents, ensuring they implement core methods for creation, execution, and management.

*   **`generic_agent.py`**: Provides `GenericAgent`, a concrete implementation of `BaseAgent`. This ready-to-use agent handles the entire lifecycle, including:
    *   Dynamic agent creation, updates, and deletion.
    *   Thread management for conversations.
    *   Resilient execution with built-in retries for transient errors.
    *   File management for tools like Code Interpreter.

#### Usage Example:

```python
from azure.ai.projects.aio import AIProjectClient
from src.factory.agents.ai_projects.generic_agent import GenericAgent
from src.factory.config.app_config import config

# Initialize the AI Project client
client = AIProjectClient(endpoint=config.AZURE_OPENAI_ENDPOINT, credential=...)

# Create a generic agent instance
agent = GenericAgent(project_client=client, model="gpt-4o", name="my-generic-agent")

# Get a thread and run the agent
thread = await agent.get_thread()
response = await agent.run("Hello, what can you do?", thread)
print(response)
```

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
