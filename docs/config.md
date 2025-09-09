# Config Module

The `config` module provides a centralized and robust system for managing application settings. It loads configuration from environment variables and `.env` files, ensuring that secrets and settings are handled securely and efficiently.

## Key Components

-   **`app_config.py`**: The core of the module, this file defines the `AppConfig` class. This class lazy-loads all configuration properties, making them accessible as class attributes. It ensures that required settings are present and provides sensible defaults for optional ones.

-   **`secret_config.py`**: A helper utility for fetching secrets from a secure, external location like Akeyless or Azure Key Vault. It is designed to read secrets from a mounted filesystem path (e.g., `/etc/secrets`), which is a common pattern in containerized environments.

## Features

-   **Unified Access**: Provides a single, consistent interface (`config`) to access all application settings.
-   **Environment-Aware**: Automatically loads variables from a `.env` file for local development while prioritizing system environment variables in production.
-   **Secret Management**: Integrates with external secret stores for handling sensitive data like API keys.
-   **Lazy Loading**: Configuration values are loaded on-demand, improving startup time.
-   **Telemetry Integration**: Logs warnings if required configuration values are missing, aiding in quick diagnostics.

## Usage

To use the configuration module, simply import the global `config` object from `app_config.py`.

```python
from factory.config.app_config import config

# Access a required setting
# The application will raise a ValueError at startup if this is not set
openai_key = config.OPENAI_API_KEY

# Access an optional setting with a default value
# If not set, this will return an empty string or a predefined default
app_insights_key = config.APPLICATION_INSIGHTS_CONNECTION_STRING

# Use settings to configure a client
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
```

## Environment Variables

The module is configured via environment variables. For a complete list, see the main `README.md` or the `.env.sample` file.

-   `DEFAULT_PROVIDER_TYPE`: Specifies the primary LLM provider (`azure_openai`, `azure-ai-inference`, etc.).
-   `AZURE_OPENAI_API_KEY`: API key for Azure OpenAI services.
-   `COSMOS_DB_ENDPOINT`: Endpoint for the Cosmos DB memory store.
-   `APPLICATIONINSIGHTS_CONNECTION_STRING`: Connection string for Azure Application Insights.
