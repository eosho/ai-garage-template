# Logger Module Documentation

The `logger` module provides a centralized, factory-based system for configuring and using structured logging and distributed tracing. It is built on top of the standard Python `logging` library and `OpenTelemetry`, with first-class support for Azure Monitor.

## Core Concepts

1.  **`LoggingFactory`**: A singleton class that acts as the central configuration point for all telemetry. It ensures that logging and tracing are initialized only once in an application's lifecycle (`idempotent setup`).

2.  **Unified Configuration**: The factory's `configure` method is the single entry point for setting up telemetry. It allows you to specify a default logging level and a tracing backend.

3.  **Multiple Backends (`TracingProvider`)**: The module supports different backends for different environments:
    *   `TracingProvider.AZURE_MONITOR`: The default and recommended provider for production. It sends logs and traces to Azure Application Insights using the `azure-monitor-opentelemetry` SDK. It requires the `APPLICATIONINSIGHTS_CONNECTION_STRING` environment variable.
    *   `TracingProvider.CONSOLE`: A simple provider for local development. It prints all traces to the console, making it easy to debug without needing an external service.
    *   `TracingProvider.NONE`: Disables tracing entirely.

4.  **Standardized Access**: Once configured, you can get pre-configured `logger` and `tracer` instances from anywhere in your application using `LoggingFactory.get_logger(__name__)` and `LoggingFactory.get_tracer(__name__)`. This ensures all parts of the application use the same telemetry setup.

5.  **Resource Metadata**: Telemetry is automatically enriched with metadata about the application, such as `service.name`, `service.version`, and `deployment.environment`, which are read from environment variables. This is crucial for filtering and analyzing telemetry data in a monitoring tool.

## Directory Structure

```
logger/
├── enums.py        # Defines enums like TelemetryLevel and TracingProvider
├── telemetry.py    # Contains the LoggingFactory and its configuration logic
└── __init__.py
```

---

## How It Works: The Flow

1.  **Application Startup**: At the very beginning of the application's lifecycle, `LoggingFactory.configure()` is called.
2.  **Configuration**: You pass a `TelemetryLevel` (e.g., `INFO`, `DEBUG`) and a `TracingProvider` (e.g., `AZURE_MONITOR`).
3.  **Backend Setup**: The factory checks which provider was selected.
    *   If `AZURE_MONITOR`, it calls `configure_azure_monitor()`, which automatically sets up the necessary exporters and processors to send data to Application Insights.
    *   If `CONSOLE`, it sets up a `ConsoleSpanExporter` to print traces to the terminal.
4.  **Handler Configuration**: The factory ensures a standard `StreamHandler` is attached to the root logger, so that logs are visible in the console regardless of the tracing backend.
5.  **Flagging**: The factory sets an internal flag (`_is_configured`) to `True` to prevent re-initialization.
6.  **Runtime Usage**:
    *   A module calls `LoggingFactory.get_logger(__name__)` to get a standard `Logger` instance.
    *   It calls `LoggingFactory.get_tracer(__name__)` to get an `opentelemetry.trace.Tracer` instance.
    *   These instances are now ready to be used for logging messages or creating trace spans, and the data will be sent to the configured backend.

## Usage Example

This example shows how to configure the `LoggingFactory` at startup and use it in a function.

```python
from src.factory.logger.telemetry import LoggingFactory, TelemetryLevel, TracingProvider
import os

def initialize_app():
    """
    Configure telemetry once at application startup.
    """
    # For production, you would use AZURE_MONITOR.
    # The connection string must be set as an environment variable.
    provider = TracingProvider.AZURE_MONITOR
    
    # For local development, use the console.
    if not os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"):
        print("App Insights connection string not found. Falling back to console.")
        provider = TracingProvider.CONSOLE

    LoggingFactory.configure(
        default_level=TelemetryLevel.INFO.value,
        tracing_provider=provider
    )
    print("Telemetry configured.")

def do_some_work():
    """
    An example function that uses the configured logger and tracer.
    """
    # Get the logger and tracer instances. They are already configured.
    logger = LoggingFactory.get_logger(__name__)
    tracer = LoggingFactory.get_tracer(__name__)

    # Start a new trace span for this operation.
    with tracer.start_as_current_span("do_some_work_span") as span:
        logger.info("Starting the work...")
        
        # Add attributes to the span for more context.
        span.set_attribute("work.type", "example")

        # Simulate some work.
        try:
            result = 10 / 2
            logger.info(f"Work completed with result: {result}")
            span.set_attribute("work.result", result)
        except Exception as e:
            logger.error("An error occurred during work.", exc_info=True)
            # Record the exception in the trace span.
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR, "An error occurred"))
        
        logger.info("Finished the work.")

# --- Application Entry Point ---
if __name__ == "__main__":
    initialize_app()
    do_some_work()
```

---

## Environment Variables

The `logger` module relies on the following environment variables for configuration:

*   `APPLICATIONINSIGHTS_CONNECTION_STRING`: **Required** for the `AZURE_MONITOR` provider. This is the unique connection string for your Application Insights resource in Azure.
*   `APP_NAME`: The name of your service (e.g., `"hazard-detection-api"`). Defaults to `"my_app"`.
*   `APP_VERSION`: The version of your application (e.g., `"1.2.0"`). Defaults to `"1.0.0"`.
*   `APP_ENV`: The environment where the app is running (e.g., `"production"`, `"staging"`). Defaults to `"development"`.
