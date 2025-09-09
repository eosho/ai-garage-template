"""
Simple Prompt Manager for handling string prompts and prompty files using Azure AI Inference.
"""

import os
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from azure.ai.inference.prompts._patch import PromptTemplate


class PromptManagerError(Exception):
    """Base exception for prompt manager errors."""


class PromptNotFoundError(PromptManagerError):
    """Raised when a requested prompt is not found."""


class PromptRenderError(PromptManagerError):
    """Raised when rendering a prompt fails."""


class PromptSourceType(Enum):
    """Supported prompt source types."""
    STRING = "string"
    PROMPTY = "prompty"


class PromptManager:
    """Simple manager for creating and handling prompts using Azure AI Inference."""

    def __init__(self, prompts_directory: Optional[str] = None):
        """
        Initialize the PromptManager.

        Args:
            prompts_directory: Optional directory path where prompty files are stored
        """
        self.prompts_directory = Path(prompts_directory) if prompts_directory else None
        self._template_cache: Dict[str, PromptTemplate] = {}
        self._registered_prompts: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def from_directory(cls, directory: str) -> 'PromptManager':
        """Create a PromptManager from a directory.
        
        Args:
            directory: Directory path where prompty files are stored.
        """
        return cls(prompts_directory=directory)

    def create_from_string(self, prompt_template: str) -> PromptTemplate:
        """Create a PromptTemplate from an inline string.

        Args:
            prompt_template: The prompt template string.
        """
        try:
            return PromptTemplate.from_string(prompt_template=prompt_template)
        except Exception as e:
            raise PromptRenderError(f"Failed to create template from string: {e}") from e

    def create_from_prompty_file(self, file_path: str, use_cache: bool = True) -> PromptTemplate:
        """Create a PromptTemplate from a prompty file.

        Args:
            file_path: Path to the prompty file.
            use_cache: Whether to cache the loaded template for future use.

        Returns:
            PromptTemplate: The loaded prompt template.

        Raises:
            PromptNotFoundError: If the file does not exist.
        """
        try:
            # Resolve file path
            if self.prompts_directory and not os.path.isabs(file_path):
                full_path = self.prompts_directory / file_path
            else:
                full_path = Path(file_path)

            full_path_str = str(full_path)

            # Check if file exists
            if not full_path.exists():
                raise PromptNotFoundError(f"Prompt file not found: {full_path_str}")

            # Check cache first
            if use_cache and full_path_str in self._template_cache:
                return self._template_cache[full_path_str]

            # Create template from file
            template = PromptTemplate.from_prompty(full_path_str)

            # Cache if requested
            if use_cache:
                self._template_cache[full_path_str] = template

            return template

        except PromptNotFoundError:
            raise
        except Exception as e:
            raise PromptRenderError(f"Failed to create template from file '{file_path}': {e}") from e

    def generate_messages(
        self,
        template: Union[PromptTemplate, str],
        variables: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[Dict[str, str]]:
        """Generate messages from a template with provided variables.

        Args:
            template: The PromptTemplate instance or a prompt string.
            variables: Optional variables to render the prompt.
            **kwargs: Additional variables to render the prompt.

        Returns:
            List[Dict[str, str]]: Generated messages.

        Raises:
            PromptNotFoundError: If the prompt template is not found.
        """
        try:
            if variables is None:
                variables = {}

            # Merge variables and kwargs
            all_variables = {**variables, **kwargs}

            # Create template if string provided
            if isinstance(template, str):
                template = self.create_from_string(template)

            return template.create_messages(**all_variables)

        except Exception as e:
            if isinstance(e, (PromptNotFoundError, PromptRenderError)):
                raise
            raise PromptRenderError(f"Failed to generate messages: {e}") from e

    def register_prompt(self, name: str, source: str, source_type: PromptSourceType) -> None:
        """Register a prompt with the manager for easy retrieval.

        Args:
            name: Name to register the prompt under.
            source: The prompt source, either a string or file path.
            source_type: Type of the source (STRING or PROMPTY).

        Raises:
            ValueError: If the source_type is not supported.
        """
        self._registered_prompts[name] = {
            'source': source,
            'source_type': source_type
        }

    def get_registered_prompt(self, name: str) -> PromptTemplate:
        """Get a registered prompt by name.

        Args:
            name: Name of the registered prompt.

        Returns:
            PromptTemplate: The registered prompt template.

        Raises:
            PromptNotFoundError: If the prompt name is not registered.
        """
        if name not in self._registered_prompts:
            raise PromptNotFoundError(f"Prompt '{name}' is not registered")

        prompt_info = self._registered_prompts[name]
        source_type = prompt_info['source_type']
        source = prompt_info['source']

        if source_type == PromptSourceType.STRING:
            return self.create_from_string(source)
        elif source_type == PromptSourceType.PROMPTY:
            return self.create_from_prompty_file(source)
        else:
            raise PromptManagerError(f"Unsupported source type: {source_type}")

    # Convenience methods
    def create_and_generate(self, prompt_template: str, variables: Optional[Dict[str, Any]] = None, **kwargs) -> List[Dict[str, str]]:
        """Create a template from string and generate messages in one call.

        Args:
            prompt_template: The prompt template string.
            variables: Optional variables to render the prompt.
            **kwargs: Additional variables to render the prompt.

        Returns:
            List[Dict[str, str]]: Generated messages.
        """
        template = self.create_from_string(prompt_template)
        return self.generate_messages(template, variables, **kwargs)

    def load_and_generate(self, file_path: str, variables: Optional[Dict[str, Any]] = None, **kwargs) -> List[Dict[str, str]]:
        """Load a prompty file and generate messages in one call.

        Args:
            file_path: Path to the prompty file.
            variables: Optional variables to render the prompt.
            **kwargs: Additional variables to render the prompt.

        Returns:
            List[Dict[str, str]]: Generated messages.
        """
        template = self.create_from_prompty_file(file_path)
        return self.generate_messages(template, variables, **kwargs)

    def generate_from_registered(self, name: str, variables: Optional[Dict[str, Any]] = None, **kwargs) -> List[Dict[str, str]]:
        """Generate messages from a registered prompt.

        Args:
            name: Name of the registered prompt.
            variables: Optional variables to render the prompt.
            **kwargs: Additional variables to render the prompt.

        Raises:
            PromptNotFoundError: If the prompt name is not registered.

        Returns:
            List[Dict[str, str]]: Generated messages.
        """
        template = self.get_registered_prompt(name)
        return self.generate_messages(template, variables, **kwargs)

    @staticmethod
    def get_template_info(template: PromptTemplate) -> Dict[str, Any]:
        """Get information about a prompt template.

        Args:
            template: The PromptTemplate instance.

        Returns:
            Dict[str, Any]: Information about the template such as model name and parameters.
        """
        info = {}
        if hasattr(template, 'model_name') and template.model_name:
            info['model_name'] = template.model_name
        if hasattr(template, 'parameters') and template.parameters:
            info['parameters'] = template.parameters
        return info

    def clear_cache(self) -> int:
        """Clear the template cache and return number of cleared items."""
        cache_size = len(self._template_cache)
        self._template_cache.clear()
        return cache_size

    def list_registered_prompts(self) -> List[str]:
        """Get a list of registered prompt names."""
        return list(self._registered_prompts.keys())


# Simple utility functions
@staticmethod
def create_simple_prompt(system_message: str, user_message: str = "{{user_input}}") -> str:
    """Create a simple two-role prompt template.

    Args:
        system_message: The system role message.
        user_message: Placeholder for user input.

    Returns:
        str: The formatted simple prompt.
    """
    return f"""system:
{system_message}

user:
{user_message}"""


@staticmethod
def create_assistant_prompt(name: str = "{{name}}", role: str = "helpful assistant", user_message: str = "{{user_message}}") -> str:
    """Create a standard assistant prompt template.

    Args:
        name: Placeholder for user's name.
        role: Role of the assistant.
        user_message: Placeholder for user's message.

    Returns:
        str: The formatted assistant prompt.
    """
    return f"""system:
You are a {role}.
The user's name is {name}.

user:
{user_message}"""