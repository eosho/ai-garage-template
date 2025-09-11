# Memory Module Documentation

The `memory` module provides a standardized way to manage persistent, long-term memory for AI agents. It uses a factory pattern to create different memory providers, allowing the application to easily switch between storage backends like Cosmos DB for production and local JSON files for development.

## Core Concepts

1.  **Abstract Interface (`MemoryProviderBase`)**: This abstract base class defines the essential contract for any memory provider. It mandates the implementation of two core methods:
    *   `save(session_id: str, data: dict)`: Saves a dictionary of state data for a given session.
    *   `load(session_id: str) -> dict`: Loads the state data for a given session.
    This abstraction ensures that the application's business logic for state management remains independent of the underlying storage technology.

2.  **Concrete Providers**: These are the actual implementations of `MemoryProviderBase`.
    *   `CosmosMemoryProvider`: Stores session data in an Azure Cosmos DB container. It is the recommended provider for scalable, cloud-native applications. It requires configuration for the endpoint, key, database, and container.
    *   `JSONMemoryProvider`: A simple provider that stores all session data in a single local JSON file. It is ideal for local development, testing, and scenarios where no external dependencies are desired.

3.  **`MemoryFactory`**: This factory class is responsible for creating and initializing the correct memory provider based on the application's configuration. It reads the `DEFAULT_MEMORY_PROVIDER` setting and instantiates the corresponding provider class with the necessary parameters.

## Directory Structure

```
memory/
├── providers/
│   ├── cosmos_provider.py  # Provider for Azure Cosmos DB
│   └── json_provider.py    # Provider for local JSON file storage
├── base_provider.py        # The MemoryProviderBase abstract class
├── factory.py              # The MemoryFactory
└── __init__.py
```

---

## How It Works: The Flow

1.  **Configuration**: The application's configuration (via `AppConfig`) specifies the desired memory provider in the `DEFAULT_MEMORY_PROVIDER` variable (e.g., `"cosmosdb"` or `"json"`).
2.  **Factory Invocation**: An application component calls `MemoryFactory().init(...)`, passing in the required parameters for the configured store (e.g., Cosmos DB credentials or a file path).
3.  **Provider Selection**: The factory checks the `memory_store` argument and selects the appropriate provider class.
4.  **Instantiation**: It creates an instance of the selected provider (`CosmosMemoryProvider` or `JSONMemoryProvider`), passing the relevant arguments to its constructor.
5.  **Return**: The factory returns the fully configured memory provider instance.
6.  **Usage**: The application can now use the `save` and `load` methods on the returned provider to manage agent state without needing to know if the data is being written to Azure or a local file.

## Usage Example

This example demonstrates how to use the `MemoryFactory` to create a memory provider and then use it to save and load an agent's conversation history.

```python
from factory.memory.factory import MemoryFactory
from factory.config.app_config import config

async def manage_session_state(session_id: str):
    """
    Saves and loads conversation history for a given session.
    """
    try:
        # 1. Create the memory provider using the factory.
        # The factory reads the default provider type from config.
        memory_provider = MemoryFactory().init(
            memory_store=config.DEFAULT_MEMORY_PROVIDER,
            # Pass all potential parameters; the factory will use the correct ones.
            endpoint=config.COSMOS_DB_ENDPOINT,
            key=config.COSMOS_DB_KEY,
            database="AgentState",
            container="Conversations",
            file_path="local_memory.json"
        )

        # 2. Load existing state for the session.
        initial_state = await memory_provider.load(session_id)
        print(f"Initial state: {initial_state}")

        # 3. Update the state.
        updated_history = initial_state.get("history", [])
        updated_history.append({"role": "user", "content": "Hello, world!"})
        new_state = {"history": updated_history}

        # 4. Save the new state.
        await memory_provider.save(session_id, new_state)
        print(f"Saved new state for session {session_id}.")

        # 5. Verify by loading again.
        final_state = await memory_provider.load(session_id)
        print(f"Final state: {final_state}")

    except ValueError as e:
        print(f"Configuration Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# Example call for a user session
await manage_session_state("user_12345")
```

---

## Configuration

The `memory` module is configured via the central `AppConfig` and the following environment variables:

*   `DEFAULT_MEMORY_PROVIDER`: **Required**. Specifies which memory provider to use.
    *   `"cosmosdb"`: Use Azure Cosmos DB.
    *   `"json"`: Use a local JSON file.

*   `COSMOS_DB_ENDPOINT`: Required if `DEFAULT_MEMORY_PROVIDER` is `"cosmosdb"`.
*   `COSMOS_DB_KEY`: Required if `DEFAULT_MEMORY_PROVIDER` is `"cosmosdb"`.

The `database` and `container` for Cosmos DB, or the `file_path` for the JSON provider, are typically passed at runtime during factory initialization, as they can vary depending on the use case.
