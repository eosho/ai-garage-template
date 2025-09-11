# enums.py

"""
Telemetry Levels Module.

Defines standardized logging levels for telemetry configuration,
based on the Python `logging` module. Provides an enum for
consistent usage across the codebase.
"""

import logging
from enum import Enum


class TelemetryLevel(Enum):
    """Standardized logging levels for telemetry configuration."""

    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


"""
Tracing Providers Module.

Defines available tracing backends for distributed tracing.
Supports Azure Monitor, console output, and disabling telemetry.
"""

class TracingProvider(Enum):
    """Available tracing backends."""

    AZURE_MONITOR = "azure_monitor"
    CONSOLE = "console"
    NONE = "none"
