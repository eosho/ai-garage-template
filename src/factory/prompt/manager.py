"""
Prompt Manager Module.

Centralized registry for LLM prompts with support for multiple source types:
    * Inline strings (STRING).
    * Jinja2 templates (.jinja2 files).

Example:
    >>> PromptManager.register_prompt("greet", "Hello {{ name }}!", PromptSourceType.STRING)
    >>> PromptManager.get_prompt("greet", name="Flo")
    'Hello Flo!'
    >>> pm = PromptManager()
    >>> pm.greet(name="Flo")
    'Hello Flo!'
"""

import os

from pathlib import Path
from typing import Dict, Union, Optional, Any, Tuple
from enum import Enum
from jinja2 import Template, StrictUndefined
from src.factory.logger.telemetry import telemetry


# Get a logger and tracer
logger = telemetry.get_logger(__name__)
tracer = telemetry.get_tracer(__name__)


class PromptManagerError(Exception):
    """Base exception for prompt manager errors."""


class PromptNotFoundError(PromptManagerError):
    """Raised when a requested prompt is not registered."""


class PromptRenderError(PromptManagerError):
    """Raised when rendering a prompt fails."""


class PromptSourceType(str, Enum):
    """Supported prompt source types."""
    STRING = "string"
    JINJA2 = "jinja2"


class PromptManager:
    """Centralized prompt registry and renderer (singleton-like)."""

    # (namespace, name) → {"template": Template, "raw": str, "meta": dict}
    _prompts: Dict[Tuple[str, str], Dict[str, Any]] = {}

    @classmethod
    def register_prompt(
        cls,
        name: str,
        source: Union[str, Path],
        source_type: PromptSourceType = PromptSourceType.STRING,
        variable: Optional[str] = None,
        namespace: str = "default",
    ) -> None:
        """Register a prompt.

        Args:
            name: Logical name for the prompt (e.g., "greet").
            source: Path, key, or raw string depending on source type.
            source_type: Type of source (STRING, JINJA2, ENV, YAML, JSON).
            variable: Key for YAML/JSON files if multiple prompts are defined.
            namespace: Optional grouping of prompts (default "default").

        Raises:
            PromptRenderError: If template fails pre-validation.
            ValueError: If source type is unsupported.
        """
        try:
            raw_template = cls._load_source(source, source_type, variable)
            # Precompile template with strict undefined
            template_obj = Template(raw_template, undefined=StrictUndefined)

            cls._prompts[(namespace, name)] = {
                "template": template_obj,
                "raw": raw_template,
                "meta": {
                    "source": source,
                    "source_type": source_type,
                    "variable": variable,
                },
            }

            logger.info(
                "Registered prompt '%s' (ns=%s, type=%s)",
                name,
                namespace,
                source_type.value,
            )

        except Exception as e:
            logger.error("Failed to register prompt '%s': %s", name, e, exc_info=True)
            raise PromptRenderError(f"Failed to register prompt '{name}'") from e

    @classmethod
    def get_prompt(
        cls,
        prompt_name: str,
        namespace: str = "default",
        **kwargs: Any,
    ) -> str:
        """Retrieve and render a registered prompt.

        Args:
            name: Name of the prompt.
            namespace: Namespace grouping (default "default").
            **kwargs: Dynamic values to inject into the template.

        Returns:
            Rendered prompt string.

        Raises:
            PromptNotFoundError: If prompt not registered.
            PromptRenderError: If rendering fails (missing vars, bad template).
        """
        key = (namespace, prompt_name)
        if key not in cls._prompts:
            logger.warning("Prompt not found: %s (ns=%s)", prompt_name, namespace)
            raise PromptNotFoundError(f"Prompt '{prompt_name}' not registered (ns={namespace})")

        try:
            template_obj: Template = cls._prompts[key]["template"]
            rendered = template_obj.render(**kwargs)
            logger.debug("Rendered prompt '%s' (ns=%s)", prompt_name, namespace)
            return rendered
        except Exception as e:
            logger.error("Error rendering prompt '%s': %s", prompt_name, e, exc_info=True)
            raise PromptRenderError(f"Failed to render prompt '{prompt_name}'") from e

    def __getattr__(self, name: str):
        """
        Dynamically resolve prompt accessors.

        Example:
            Instead of calling:
                self.prompt_manager.get_prompt("demo_prompt")
            You can simply do:
                self.prompt_manager.demo_prompt()

        Args:
            name (str): The name of the prompt function being accessed.

        Returns:
            Callable: A wrapper function that injects kwargs into the prompt template.
        """

        def wrapper(**kwargs):
            return self.get_prompt(name, **kwargs)
        return wrapper

    @classmethod
    def list_prompts(cls) -> Dict[Tuple[str, str], str]:
        """List all registered prompts."""
        return {k: v["raw"] for k, v in cls._prompts.items()}

    @classmethod
    def reload_prompts(cls) -> None:
        """Reload all file-based prompts (JINJA2, YAML, JSON)."""
        reloaded = 0
        for key, data in cls._prompts.items():
            meta = data["meta"]
            source_type = meta["source_type"]
            if source_type in (PromptSourceType.JINJA2):
                try:
                    raw_template = cls._load_source(meta["source"], source_type, meta["variable"])
                    template_obj = Template(raw_template, undefined=StrictUndefined)
                    cls._prompts[key]["template"] = template_obj
                    reloaded += 1
                    logger.info("Reloaded prompt '%s' (ns=%s)", key[1], key[0])
                except Exception as e:
                    logger.error("Failed to reload prompt '%s': %s", key[1], e, exc_info=True)
        logger.info("Reload complete. %d prompt(s) reloaded.", reloaded)

    @staticmethod
    def _load_source(source: Union[str, Path], source_type: PromptSourceType, variable: Optional[str]) -> str:
        """
        Load a source based on its type.

        Args:
            source (Union[str, Path]): The source to load (file path or string).
            source_type (PromptSourceType): The type of the source (e.g., JINJA2).
            variable (Optional[str]): The specific variable to extract (if any).

        Returns:
            str: The loaded source content.
        """
        if source_type == PromptSourceType.STRING:
            return str(source)
        if source_type == PromptSourceType.JINJA2:
            return PromptManager._load_from_file(source)
        raise ValueError(f"Unsupported source type: {source_type}")

    @staticmethod
    def _load_from_file(file_path: Union[str, Path]) -> str:
        """Load a file and return the content as a string.

        Args:
            file_path (Union[str, Path]): The path to the file.

        Returns:
            str: The content of the file.
        """
        return Path(file_path).read_text(encoding="utf-8")