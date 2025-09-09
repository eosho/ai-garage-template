# LLM Module Documentation

The `llm` module provides a robust, factory-based system for interacting with various Large Language Models (LLMs) through a unified, abstract interface. It is designed to be extensible, configurable, and observable.

## Core Concepts

1.  **Unified Interface (`LLMProviderBase`)**: Defines a common contract for all LLM providers. This ensures that application code can interact with any supported LLM backend (e.g., Azure OpenAI, OpenAI, Azure AI Inference) without needing to know the specific implementation details. The core method is `get_completion`, which handles the logic for sending prompts and receiving responses.

2.  **Provider Implementations**: Concrete classes that implement `LLMProviderBase` for a specific backend.
    *   `AzureInferenceProvider`: Connects to models deployed via the Azure AI Inference service.
    *   `OpenAIProvider`: Connects to the standard OpenAI API (or Azure-hosted OpenAI deployments).
    *   `AzureAIProjectProvider`: Integrates with agents and models within an Azure AI Project.

3.  **Factory (`LLMFactory`)**: The central component that instantiates and configures the correct LLM provider. It reads the application's configuration (`AppConfig`) to determine which provider to use and automatically injects the necessary clients and settings. This decouples the application logic from the provider setup.

4.  **Model Configuration (`LLMModelConfig`)**: A metadata system that tracks the capabilities of different models (e.g., `gpt-4o`, `gpt-35-turbo`). It stores information on whether a model supports features like function calling, reasoning, or structured outputs. The factory uses this to validate that a requested feature is supported by the selected model, preventing runtime errors.

5.  **Telemetry**: The module is instrumented with structured logging and distributed tracing via the `LoggingFactory`. This provides deep visibility into provider creation, LLM requests, and potential errors, which is critical for debugging and monitoring.

## Directory Structure

```
llm/
├── providers/
│   ├── azure_ai_project_provider.py  # Provider for Azure AI Projects
│   ├── azure_inference_provider.py   # Provider for Azure AI Inference
│   └── openai_provider.py            # Provider for OpenAI/Azure OpenAI
├── base_provider.py                  # Abstract base class for all providers
├── client_helper.py                  # Helpers for client instantiation
├── factory.py                        # The main LLMFactory
├── llm_model_config.py               # Model capability definitions
└── __init__.py
```

---

## How It Works: The Flow

1.  **Initialization**: An application component needs to interact with an LLM.
2.  **Factory Invocation**: It calls `LLMFactory.create_llm_provider()`.
3.  **Configuration Reading**: The factory reads `config.DEFAULT_PROVIDER` (e.g., `"azure_openai"`) and `config.AZURE_OPENAI_DEPLOYMENT` (e.g., `"gpt-4o"`) from the central `AppConfig`.
4.  **Model Capability Check**: It looks up `"gpt-4o"` in its `LLM_MODELS` registry to get its `LLMModelConfig` and verify the model is supported.
5.  **Provider Selection**: Based on the provider type, the factory calls the appropriate internal creation method (e.g., `_create_openai_provider`).
6.  **Client Instantiation**: The creation method initializes the required SDK client (e.g., `AsyncAzureOpenAI`) with the correct endpoint and credentials.
7.  **Provider Instantiation**: It creates an instance of the provider class (e.g., `OpenAIProvider`), passing the client and the model's configuration.
8.  **Return**: The factory returns the fully configured provider instance, ready to be used.
9.  **LLM Interaction**: The application calls `provider.get_completion(...)`, passing prompts and parameters. The provider translates the request into the format expected by its specific backend, makes the API call, and returns a normalized response.

## Usage Example

This example demonstrates how to use the factory to get a provider and perform a completion. The factory handles all the backend complexity.

```python
from src.factory.llm.factory import LLMFactory
from src.factory.config.app_config import config

async def get_summary(text: str):
    """
    Uses the configured LLM provider to generate a summary.
    """
    try:
        # 1. The factory reads config and creates the appropriate provider
        #    (e.g., OpenAIProvider for "gpt-4o").
        provider = await LLMFactory.create_llm_provider()

        # 2. The provider's get_completion method is called.
        #    It knows how to format the request for the target model.
        response = await provider.get_completion(
            system_prompt="You are an expert summarizer.",
            user_prompt=f"Please summarize the following text in one sentence: {text}",
            max_completion_tokens=50,
            temperature=0.7
        )
        
        print(f"Summary: {response}")
        return response

    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# Example call
await get_summary("The quick brown fox jumps over the lazy dog. This classic pangram contains all the letters of the English alphabet.")
```

---

## Key Components Deep Dive

#### `LLMFactory`

*   **`create_llm_provider()`**: The primary static method. It's the single entry point for creating any LLM provider. It contains the `if/elif/else` logic to select the provider based on the `DEFAULT_PROVIDER` setting.
*   **`_create_*_provider()`**: Private static methods responsible for the specific setup of each provider (e.g., `_create_azure_inference_provider`). They handle client initialization and dependency injection.

#### `LLMProviderBase` (Abstract Base Class)

*   **`get_completion()`**: The abstract method that all concrete providers must implement. It defines a standardized signature for making LLM calls, abstracting away differences in how various APIs handle parameters like `max_tokens`, `temperature`, etc.

#### `LLMModelConfig`

*   This is a data class that acts as a schema for model capabilities.
*   **`LLM_MODELS`**: A dictionary that maps model names (e.g., `"gpt-4o"`) to `LLMModelConfig` instances. This registry is the single source of truth for what each model can do.
    ```python
    LLM_MODELS = {
        "gpt-4o": LLMModelConfig(
            name="gpt-4o",
            # ... capabilities ...
            supports_reasoning=True,
            supports_function_calling=True,
        ),
        # ... other models
    }
    ```

This structure makes the `llm` module highly modular and easy to maintain. To add a new LLM backend, one only needs to create a new provider class, add its configuration to `AppConfig`, and update the factory.
