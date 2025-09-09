# base_agent.py

"""
BaseAgent Abstraction for Azure AI Project Agents.

This module defines the abstract `BaseAgent` class, which specifies the
contract for building agents that integrate with Azure AI Projects.
It enforces consistency across all agent implementations and ensures that
core lifecycle methods are implemented.

Features:
    * Abstract base class using Python's `abc.ABC`.
    * Defines common agent responsibilities:
        - Create and delete agents.
        - Run an agent on user input within a thread.
        - Manage threads and retrieve messages.
        - Update agent metadata and attached tools.
        - Upload files to the agent file API.
    * Provides a shared constructor to hold configuration, model,
      project client, and optional tool resources.

Classes:
    BaseAgent (ABC):
        Abstract base class that defines the required interface for
        all Azure AI Project agents.

Intended Usage:
    Subclass `BaseAgent` and implement all abstract methods to provide
    a concrete agent with custom behavior. The `GenericAgent` class
    (see `generic_agent.py`) is an example implementation.

Example:
    >>> from azure.ai.projects.aio import AIProjectClient
    >>> from src.agents.base_agent import BaseAgent

    >>> class MyAgent(BaseAgent):
    ...     async def create(...): ...
    ...     async def run(...): ...
    ...     async def get_messages(...): ...
    ...     async def get_thread(...): ...
    ...     async def update(...): ...
    ...     async def delete(...): ...
    ...     async def get_agent(...): ...
    ...     async def upload_file(...): ...
    ...
    >>> client = AIProjectClient(endpoint="...", credential="...")
    >>> my_agent = MyAgent(project_client=client, model="gpt-4o", name="custom-agent")
"""

from typing import Optional
from abc import ABC, abstractmethod
from azure.ai.projects.aio import AIProjectClient
from azure.ai.agents.models import (
    ResponseFormatJsonSchemaType,
    AgentThread,
    Agent
)

class BaseAgent(ABC):
    """Abstract base class for Azure AI Project agents."""

    def __init__(
        self,
        project_client: AIProjectClient,
        model: str,
        name: str,
        agent_id: Optional[str] = None,
        instructions: Optional[str] = None,
        description: Optional[str] = None,
        response_format: Optional[ResponseFormatJsonSchemaType] = None,
        tools: Optional[list] = None,
        tool_resources: Optional[dict] = None,
    ) -> None:
        self.project_client = project_client
        self.model = model
        self.name = name
        self.agent_id = agent_id
        self.instructions = instructions
        self.description = description
        self.response_format = response_format
        self.tools = tools
        self.tool_resources = tool_resources
        self.thread_id: Optional[str] = None

    @abstractmethod
    async def create(
        self,
        name: str,
        instructions: str,
        tools: Optional[list] = None,
    ) -> Agent:
        """Create a new agent."""
        ...

    @abstractmethod
    async def run(
        self,
        user_message: str,
        thread: AgentThread,
        tools: Optional[list] = None,
    ) -> str:
        """Run the agent on a user message."""
        ...

    @abstractmethod
    async def get_messages(self, thread: AgentThread) -> str:
        """Get messages from a thread."""
        ...

    @abstractmethod
    async def get_thread(self) -> AgentThread:
        """Get the current state of the agent."""
        ...

    @abstractmethod
    async def update(
        self,
        name: str,
        agent_id: str,
        instructions: Optional[str] = None,
        tools: Optional[list] = None
    ) -> Agent:
        """Update the agent metadata, model deployment, or tools."""
        ...

    @abstractmethod
    async def delete(self, agent_id: str) -> None:
        """Delete the agent."""
        ...

    @abstractmethod
    async def get_agent(self, agent_id: str) -> Agent:
        """Retrieve the agent by ID."""
        ...

    @abstractmethod
    async def upload_file(self, file: str) -> str:
        """Upload a file to the agent file API."""
        ...

    def get_instructions(self) -> Optional[str]:
        pass
