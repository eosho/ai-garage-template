import asyncio

from azure.ai.projects.aio import AIProjectClient
from factory.agents.ai_projects.generic_agent import GenericAgent
from factory.config.app_config import config
from factory.utils.clients import _get_azure_credential

from factory.memory.factory import MemoryFactory

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
            model=config.LLM_MODEL_NAME,
            name="faq-bot",
            instructions="You are a helpful bot that answers questions."
        )

        # 3. Get a conversation thread
        thread = await agent.get_thread()

        # 4. Run the agent with the user's question
        # This will create the agent, run it, and delete it automatically.
        print("Asking the agent...")
        response = await agent.run(question, thread)

        # convert response to Dict[str, Any]
        response_dict = {
            "user_id": 1,
            "question": question,
            "answer": response
        }

        # Store in memory
        memory = MemoryFactory.init(
            memory_store="json",
            file_path="src/examples/projects/memory/memory.json"
        )
        # Write to memory
        await memory.create(key=thread.id, value=response_dict)

        # Load from memory
        await memory.get(key=thread.id)

        # Close the client
        await client.close()

        print(f"\nAgent's Response:\n{response}")
        return response

    except Exception as e:
        print(f"An error occurred: {e}")

# Example call
if __name__ == "__main__":
  asyncio.run(ask_agent_a_question("What is the purpose of the Azure AI Projects SDK?"))