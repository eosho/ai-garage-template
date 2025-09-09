# telemetry.py

"""
Logging and Telemetry Factory Module.

This module provides a centralized factory for configuring both logging and
distributed tracing in applications, with first-class support for Azure
Application Insights via the Azure Monitor OpenTelemetry SDK.

Features:
    - Enum-based configuration for logging levels (TelemetryLevel) and tracing backends (TracingProvider).
    - Idempotent setup: prevents duplicate initialization of handlers and tracers.
    - Multiple tracing backends supported:
        * Azure Monitor (production / cloud deployments).
        * Console exporter (local development and debugging).
        * None (telemetry disabled).
    - Convenience methods for retrieving pre-configured loggers and tracers.
    - Standardized log level management across root and handler loggers.

Usage:
    >>> from logging_factory import LoggingFactory, TelemetryLevel, TracingProvider
    >>> LoggingFactory.configure(
    ...     default_level=TelemetryLevel.INFO.value,
    ...     tracing_provider=TracingProvider.AZURE_MONITOR
    ... )
    >>> logger = LoggingFactory.get_logger(__name__)
    >>> tracer = LoggingFactory.get_tracer(__name__)

Environment Variables:
    APPLICATIONINSIGHTS_CONNECTION_STRING (str): Required if using Azure Monitor.
        This is the connection string for sending telemetry to Azure Application Insights.
    APP_NAME (str): Optional. Service name for telemetry (default: "my_app").
    APP_VERSION (str): Optional. Service version (default: "1.0.0").
    APP_ENV (str): Optional. Deployment environment (default: "development").

This factory simplifies observability setup by enforcing consistent logging and
tracing practices across different environments (development, test, production).
"""

import os
import logging

from dotenv import load_dotenv
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)
from opentelemetry.sdk.resources import Resource

from .enums import TelemetryLevel, TracingProvider

# Load .env variables
load_dotenv()

# Suppress the Azure Monitor SDK logging
logging.getLogger("azure.monitor").setLevel(logging.WARNING)
logging.getLogger("azure.core").setLevel(logging.WARNING)
logging.getLogger("azure.identity").setLevel(logging.WARNING)
logging.getLogger("opentelemetry").setLevel(logging.WARNING)



# Define a global resource for telemetry metadata
resource = Resource.create({
    "service.name": os.getenv("APP_NAME", "my_app"),
    "service.version": os.getenv("APP_VERSION", "1.0.0"),
    "deployment.environment": os.getenv("APP_ENV", "development")
})



class LoggingFactory:
    """
    A logging factory for creating and configuring loggers and tracers
    that send telemetry to Azure Application Insights (or other backends)
    using OpenTelemetry.
    """

    _is_configured = False
    _default_level = logging.INFO
    _tracing_provider = TracingProvider.AZURE_MONITOR

    def __init__(
        self,
        default_level: TelemetryLevel = TelemetryLevel.INFO,
        tracing_provider: TracingProvider = TracingProvider.AZURE_MONITOR,
    ):
        """
        Initialize the logging factory with default log level and tracing provider.

        Args:
            default_level: The default telemetry logging level to use.
            tracing_provider: Which tracing provider to configure (Azure, Console, or None).
        """
        self.default_level = default_level.value
        self.tracing_provider = tracing_provider

        if not LoggingFactory._is_configured:
            LoggingFactory.configure(
                default_level=self.default_level,
                tracing_provider=self.tracing_provider,
            )

    @classmethod
    def configure(
        cls,
        default_level: int = logging.INFO,
        tracing_provider: TracingProvider = TracingProvider.AZURE_MONITOR,
    ):
        """
        Initializes logging and tracing for the application. Should be called once at startup.

        Args:
            default_level: The default logging level to apply to all handlers.
            tracing_provider: Which tracing backend to configure.
        """
        if cls._is_configured:
            logging.warning("Logging and tracing already configured. Skipping re-configuration.")
            return

        cls._default_level = default_level
        cls._tracing_provider = tracing_provider

        success = False
        if tracing_provider == TracingProvider.AZURE_MONITOR:
            success = cls._setup_azure_monitor_telemetry()
        elif tracing_provider == TracingProvider.CONSOLE:
            success = cls._setup_console_telemetry()
        elif tracing_provider == TracingProvider.NONE:
            logging.info("Telemetry disabled (TracingProvider.NONE).")
            success = True

        if success:
            cls._is_configured = True
            logging.info("Telemetry configured successfully with %s.", tracing_provider.value)
        else:
            logging.warning("Telemetry setup failed or skipped for %s.", tracing_provider.value)

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Returns a logger with the specified name, configured by the factory.

        Args:
            name: The name of the logger to retrieve (e.g., __name__).

        Returns:
            A configured logging.Logger instance.
        """
        if not cls._is_configured:
            cls.configure()

        return logging.getLogger(name)

    @classmethod
    def get_tracer(cls, name: str) -> trace.Tracer:
        """
        Returns a tracer with the specified name, configured by the factory.

        Args:
            name: The name of the tracer to retrieve (e.g., __name__).

        Returns:
            An opentelemetry.trace.Tracer instance.
        """
        if not cls._is_configured:
            cls.configure()

        return trace.get_tracer(name)

    @classmethod
    def _setup_stream_handler(cls):
        """
        Ensures the root logger has a default StreamHandler with a formatter.
        Prevents duplicate handlers if already present.
        """
        root_logger = logging.getLogger()
        if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter("%(asctime)s - [ %(levelname)s ] - %(name)s - %(message)s"),
            )
            root_logger.addHandler(handler)
        root_logger.setLevel(cls._default_level)

    @classmethod
    def _setup_azure_monitor_telemetry(cls) -> bool:
        """
        Configures the Azure Monitor OpenTelemetry distro.

        Returns:
            bool: True if telemetry was successfully configured, False otherwise.
        """
        connection_string = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")
        if not connection_string:
            logging.warning(
                "APPLICATIONINSIGHTS_CONNECTION_STRING not set. "
                "Telemetry will not be sent to Application Insights."
            )
            return False

        try:
            configure_azure_monitor(
                connection_string=connection_string,
                enable_live_metrics=True,
                resource=resource
            )

            cls._setup_stream_handler()

            logging.info("Azure Monitor OpenTelemetry configured.")
            return True

        except Exception as e:
            logging.error(f"Failed to configure Azure Monitor telemetry: {e}", exc_info=True)
            return False

    @classmethod
    def _setup_console_telemetry(cls) -> bool:
        """
        Configures a simple ConsoleExporter for tracing/logging.
        Useful for local development and debugging.
        """
        try:
            provider = TracerProvider(resource=resource)
            processor = BatchSpanProcessor(ConsoleSpanExporter())
            provider.add_span_processor(processor)
            trace.set_tracer_provider(provider)

            cls._setup_stream_handler()

            logging.info("Console OpenTelemetry exporter configured.")
            return True

        except Exception as e:
            logging.error(f"Failed to configure console telemetry: {e}", exc_info=True)
            return False
