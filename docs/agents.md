# Agents Module Documentation

The `agents` module provides a framework for creating and managing agents that integrate with the **Azure AI Projects** SDK. It is designed to offer both a standardized contract and a ready-to-use implementation for orchestrating agent-based workflows.

## Core Concepts

1.  **`BaseAgent` (Abstract Base Class)**: This class, located in `base_agent.py`, defines the fundamental interface that all Azure AI Project agents must implement. It establishes a contract for core agent lifecycle operations, including:
    *   `create`: Creating a new agent.
    *   `run`: Executing an agent within a conversation thread.
    *   `get_thread`: Managing conversation threads.
    *   `update`: Modifying an existing agent.
    *   `delete`: Removing an agent.
    *   `upload_file`: Sending files to the agent for tools like Code Interpreter.
    By subclassing `BaseAgent`, you ensure that your agent implementations are consistent and predictable.

2.  **`GenericAgent` (Concrete Implementation)**: Found in `generic_agent.py`, this class is a direct, reusable implementation of `BaseAgent`. It provides a complete, out-of-the-box solution for most common agent orchestration tasks. Its key features include:
    *   **Full Lifecycle Management**: Implements all abstract methods from `BaseAgent`.
    *   **Dynamic Agent Handling**: The `run` method demonstrates a common pattern where an agent is created on-the-fly for a specific task, used, and then immediately deleted. This is useful for single-purpose or "disposable" agents.
    *   **Resiliency**: The `run` method is decorated with a `tenacity` retry mechanism, which automatically retries the operation on transient `HttpResponseError` exceptions. This makes the agent more robust against temporary network or service issues.
    *   **Thread Management**: It handles the creation and retrieval of conversation threads (`AgentThread`), which are essential for maintaining context in a multi-turn dialogue.
    *   **Detailed Logging**: It provides detailed logs for agent creation, run status, tool calls, and cleanup, which is invaluable for debugging complex agent interactions.

## Directory Structure

```
agents/
└── ai_projects/
    ├── base_agent.py     # The abstract base class defining the agent interface
    └── generic_agent.py  # A concrete, reusable agent implementation
```

---

## How It Works: The `GenericAgent` Flow

The `GenericAgent` is designed to encapsulate the entire orchestration logic for a typical agent interaction.

1.  **Initialization**: You create an instance of `GenericAgent`, providing it with an `AIProjectClient`, a model deployment name (e.g., `"gpt-4o"`), and a name for the agent.
    ```python
    client = AIProjectClient(...)
    agent = GenericAgent(project_client=client, model="gpt-4o", name="data-analyst-agent")
    ```
2.  **Thread Acquisition**: Before running, you get a thread using `agent.get_thread()`. The agent will create a new thread on the first call or reuse the existing one.
3.  **Execution (`run` method)**: This is the core of the workflow.
    a. **Agent Creation**: It first calls `self.create()` to dynamically create a new agent instance on the Azure AI platform using the provided name, instructions, and tools.
    b. **Message Posting**: It posts the user's message to the thread.
    c. **Run Invocation**: It calls `project_client.agents.runs.create_and_process()`, which starts the agent's execution within the thread. This is a blocking call that waits for the run to reach a terminal state (e.g., `COMPLETED`, `FAILED`).
    d. **Response Retrieval**: If the run is successful, it calls `self.get_messages()` to fetch the last message added by the agent to the thread.
    e. **Cleanup**: In a `finally` block, it calls `self.delete()` to remove the dynamically created agent, ensuring no orphaned resources are left behind.
4.  **Return Value**: The `run` method returns the agent's final text response.

## Usage Example

This example shows how to use `GenericAgent` to create an agent that can answer a question.

```python
from azure.ai.projects.aio import AIProjectClient
from factory.agents.ai_projects.generic_agent import GenericAgent
from factory.config.app_config import config
from factory.utils.utility import _get_azure_credential

async def ask_agent_a_question(question: str):
    """
    Uses GenericAgent to get an answer from an AI agent.
    """
    try:
        # 1. Initialize the AI Project client
        credential = _get_azure_credential()
        client = AIProjectClient(
            endpoint=config.AZURE_OPENAI_ENDPOINT, 
            credential=credential
        )

        # 2. Create an instance of GenericAgent
        # The instructions for the agent are defined within the agent class
        # or passed during initialization.
        agent = GenericAgent(
            project_client=client,
            model=config.AZURE_OPENAI_DEPLOYMENT,
            name="faq-bot",
            instructions="You are a helpful bot that answers questions."
        )

        # 3. Get a conversation thread
        thread = await agent.get_thread()

        # 4. Run the agent with the user's question
        # This will create the agent, run it, and delete it automatically.
        print("Asking the agent...")
        response = await agent.run(question, thread)
        
        print(f"\nAgent's Response:\n{response}")
        return response

    except Exception as e:
        print(f"An error occurred: {e}")

# Example call
await ask_agent_a_question("What is the purpose of the Azure AI Projects SDK?")
```

This modular design allows for clear separation of concerns. The `BaseAgent` provides the architectural blueprint, while `GenericAgent` offers a powerful, reusable component for executing agent tasks. For more specialized behavior, you can create new classes that inherit from `BaseAgent` and implement their own custom logic.
