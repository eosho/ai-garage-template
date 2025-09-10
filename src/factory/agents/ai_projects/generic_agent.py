# generic_agent.py

"""
GenericAgent Implementation for Azure AI Project Orchestration.

This module provides a concrete implementation of the `BaseAgent` abstract class.
It implements agent lifecycle management, thread handling, retries, and file
operations using the Azure AI Projects SDK.

Features:
    * Implements all methods defined in `BaseAgent`.
    * Supports dynamic agent creation, execution, updating, and deletion.
    * Thread management:
        - Create or reuse threads.
        - Send and retrieve messages between user and agent.
    * Run execution:
        - Handles agent runs in threads.
        - Retry logic for transient `HttpResponseError` failures
          using the `tenacity` library.
        - Collects detailed run steps and logs tool calls.
    * File management:
        - Upload files (e.g., for tools like Code Interpreter).
        - Delete uploaded files from the agent file API.
    * Integrated telemetry via `LoggingFactory`.

Classes:
    GenericAgent (BaseAgent):
        Concrete implementation of a reusable Azure AI Project agent.

Example Usage:
    >>> from azure.ai.projects.aio import AIProjectClient
    >>> from src.agents.generic_agent import GenericAgent
    >>> from src.factory.config.app_config import config

    >>> client = AIProjectClient(endpoint=config.AZURE_OPENAI_ENDPOINT, credential="...")
    >>> agent = GenericAgent(project_client=client, model="gpt-4o", name="helper-agent")

    >>> thread = await agent.get_thread()
    >>> response = await agent.run("Hello agent!", thread)
    >>> print(response)
"""


from typing import Dict, List, Any, Optional
from azure.ai.agents.models import (
    ResponseFormatJsonSchemaType,
    AgentThread,
    Agent,
    FilePurpose,
    MessageRole,
    RunStatus
)
from azure.core.exceptions import HttpResponseError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.factory.agents.ai_projects.base_agent import BaseAgent
from src.factory.logger.telemetry import telemetry

logger = telemetry.get_logger(__name__)
tracer = telemetry.get_tracer(__name__)


class GenericAgent(BaseAgent):
    """
    GenericAgent for Azure AI Project multi-agent orchestration.

    Features:
        - Create, run, update, and delete agents dynamically.
        - Supports threads for message management.
        - Retry mechanism for resiliency (HttpResponseError + transient failures).
        - File upload API for tools like Code Interpreter.

    Attributes:
        model (str): Deployment name of the Azure OpenAI model.
        name (str): Default agent name.
        description (str): Default agent description.
        instructions (str): Default instructions for the agent.
        tools (Optional[list]): Optional tools to attach to the agent.
        tool_resources (Optional[dict]): Optional resources linked to tools.
    """

    @retry(
        retry=retry_if_exception_type(HttpResponseError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=10),
    )
    async def run(
        self,
        user_message: Any,
        thread: AgentThread,
        tools: Optional[Any] = None
    ) -> str:
        """
        Run the agent in a given thread.

        Args:
            user_message (str): The message from the user.
            thread (AgentThread): The thread in which the agent will run.
            tools (Optional[list]): Optional tools to use for this run.

        Returns:
            str: The response content from the agent.

        Raises:
            HttpResponseError: If the run fails with a retryable error.
        """
        agent_id = None
        try:
            agent_output = None
            agent = await self.create(
                name=self.name,
                instructions=self.get_instructions() or self.instructions,
                tools=tools or self.tools,
                response_format=self.response_format
            )
            agent_id = agent.id

            message = await self.project_client.agents.messages.create(
                thread_id=thread.id,
                role=MessageRole.USER,
                content=user_message,
            )
            logger.info("Created message, ID=%s", message.id)
            logger.debug("Created message, ID=%s", message.id)

            run = await self.project_client.agents.runs.create_and_process(
                thread_id=thread.id,
                agent_id=agent.id,
            )
            logger.info("Started run, ID=%s", run.id)
            logger.debug("Run status=%s for agent_id=%s", run.status, agent_id)

            if run.status == RunStatus.COMPLETED:
                agent_output = await self.get_messages(thread=thread)
            elif run.status == RunStatus.FAILED:
                logger.error("Run failed: %s", run.last_error)

            # Fetch and log run steps for debugging
            if run.id:
                await self.get_run_steps(thread.id, run.id)

            return agent_output if agent_output is not None else ""
        finally:
            if agent_id:
                logger.debug("Cleaning up agent id=%s", agent_id)
                await self.delete(agent_id)

    async def get_messages(self, thread: AgentThread) -> str:
        """
        Retrieve messages from a given thread.

        Args:
            thread (AgentThread): The thread object.
            latest (bool): If True, returns only the last agent message.

        Returns:
            str: Aggregated message content.
        """
        response_content = ""
        last_message = await self.project_client.agents.messages.get_last_message_text_by_role(
            thread_id=thread.id, role=MessageRole.AGENT
        )
        if last_message and last_message.text:
            response_content = last_message.text.value
        return response_content

    async def get_thread(self) -> AgentThread:
        """
        Get or create a thread.

        Returns:
            AgentThread: Thread object.
        """
        if not self.thread_id:
            thread = await self.project_client.agents.threads.create()
            self.thread_id = thread.id
            logger.info("Created new thread id=%s", self.thread_id)
        else:
            thread = await self.project_client.agents.threads.get(self.thread_id)
            logger.info("Using existing thread id=%s", self.thread_id)
        return thread

    async def create(
        self,
        name: Optional[str] = None,
        instructions: Optional[str] = None,
        tools: Optional[list] = None,
        response_format: Optional[ResponseFormatJsonSchemaType] = None
    ) -> Agent:
        """
        Create a new agent.

        Args:
            name: Name of the agent.
            instructions: Instructions for the agent.
            tools: Optional list of tools the agent can use.
            response_format: Optional response format schema type.

        Returns:
            Agent: The created agent definition.
        """
        agent_definition = await self.project_client.agents.create_agent(
            model=self.model,
            name=self.name or name,
            description=self.description,
            instructions=instructions or self.get_instructions(),
            tools=tools or self.tools,
            tool_resources=self.tool_resources,
            response_format=response_format,
        )
        logger.info("Created agent id=%s name=%s", agent_definition.id, agent_definition.name)
        return agent_definition

    async def delete(self, agent_id: str) -> None:
        """Delete an agent by ID.

        Args:
            agent_id (str): The ID of the agent to delete.
        """
        result = await self.project_client.agents.delete_agent(agent_id)
        logger.info("Deleted agent id=%s result=%s", agent_id, result)

    async def update(
        self,
        name: str,
        agent_id: str,
        instructions: Optional[str] = None,
        tools: Optional[list] = None,
    ) -> Agent:
        """Update an existing agent.

        Args:
            name (Optional[str]): The new name of the agent.
            agent_id (Optional[str]): The ID of the agent to update.
            instructions (Optional[str]): The new instructions for the agent.
            tools (Optional[list]): The new list of tools for the agent.
        """
        updated_agent = await self.project_client.agents.update_agent(
            agent_id=agent_id,
            name=name,
            instructions=instructions,
            tools=tools or self.tools,
        )

        # Keep the agent reference in sync if this instance manages it
        self.agent_id = updated_agent.id
        return updated_agent

    async def get_agent(self, agent_id: str) -> Agent:
        """Retrieve an agent by ID.

        Args:
            agent_id (str): The ID of the agent to retrieve.
        """
        agent_definition = await self.project_client.agents.get_agent(agent_id=agent_id)
        logger.debug("Fetched agent id=%s", agent_id)
        return agent_definition

    async def upload_file(self, file: str) -> str:
        """
        Upload a file to Azure Agent File API (e.g., for Code Interpreter tool).

        Args:
            file (str): Path to the file to upload.

        Returns:
            Optional[str]: The ID of the uploaded file or None if failed.
        """
        try:
            file_info = await self.project_client.agents.files.upload_and_poll(
                file_path=file,
                purpose=FilePurpose.AGENTS,
            )
            logger.info("Uploaded file '%s' id=%s", file, file_info.id)
            return file_info.id
        except Exception as e:
            logger.error("Failed to upload file %s: %s", file, e)
            return ""

    async def delete_uploaded_file(self, file_id: str) -> None:
        """
        Delete a previously uploaded file by its ID.

        Args:
            file_id (str): The ID of the file to delete.
        """
        try:
            await self.project_client.agents.files.delete(file_id=file_id)
            logger.info("Deleted uploaded file id=%s", file_id)
        except Exception as e:
            logger.error("Failed to delete file id=%s: %s", file_id, e)


    async def get_run_steps(self, thread_id: str, run_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve and parse detailed run steps for a given agent run.

        Args:
            thread_id (str): The ID of the thread containing the run.
            run_id (str): The ID of the run to inspect.

        Returns:
            List[Dict[str, Any]]: Parsed run step metadata, including tool calls.
                Example:
                [
                    {
                        "id": "step-123",
                        "status": "completed",
                        "tool_calls": [
                            {
                                "id": "toolcall-456",
                                "type": "function",
                                "function_name": "load_image_from_file",
                                "function_output": "{...}"
                            }
                        ]
                    }
                ]

        Raises:
            Exception: Propagates any errors from the Azure SDK after logging.
        """
        results: List[Dict[str, Any]] = []

        try:
            logger.debug("Fetching run steps for thread_id=%s run_id=%s", thread_id, run_id)

            run_steps = self.project_client.agents.run_steps.list(
                thread_id=thread_id,
                run_id=run_id,
            )

            async for step in run_steps:
                step_id = getattr(step, "id", None)
                step_status = getattr(step, "status", None)
                step_details = getattr(step, "step_details", {}) or {}

                step_info: Dict[str, Any] = {
                    "id": step_id,
                    "status": step_status,
                    "tool_calls": [],
                }

                tool_calls = step_details.get("tool_calls", [])
                if tool_calls:
                    for call in tool_calls:
                        call_id = call.get("id")
                        call_type = call.get("type")
                        function_details = call.get("function", {})

                        step_info["tool_calls"].append(
                            {
                                "id": call_id,
                                "type": call_type,
                                "function_name": function_details.get("name"),
                                "function_output": function_details.get("output"),
                            }
                        )


                logger.info("Step %s status=%s tool_calls=%s",
                            step_id, step_status, step_info["tool_calls"])

                for call in step_info["tool_calls"]:
                    logger.debug(
                        "  ToolCall id=%s type=%s function=%s output=%s",
                        call["id"], call["type"],
                        call["function_name"], call["function_output"]
                    )

                results.append(step_info)

            return results

        except Exception as e:
            logger.error(
                "Failed to retrieve run steps for thread_id=%s run_id=%s: %s",
                thread_id, run_id, e,
                exc_info=True
            )
            raise
