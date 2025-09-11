# Utils Module Documentation

The `utils` module contains shared helper functions and utilities that are used across the different modules in the `factory` package. Its primary purpose is to centralize common logic to avoid code duplication and simplify complex tasks like authentication.

## Directory Structure

```
utils/
└── clients.py  # Main file containing all client functions
```

---

## Key Components

### `_get_azure_credential()`

This is the most critical function in the `utils` module. It provides a robust and flexible way to obtain credentials for authenticating with Azure services. It simplifies the developer experience by automatically trying multiple authentication methods in a predefined order, making it seamless to run the application in different environments (local development, CI/CD pipelines, production).

#### How It Works: The Credential Chain

The function attempts to create a credential object using the following methods, stopping at the first one that succeeds:

1.  **`AzureKeyCredential`**: If an `api_key` is passed directly to the function, it will use this method. This is common for services that rely on simple API keys.

2.  **`ClientSecretCredential`**: It attempts to authenticate using a **Service Principal** by reading the following environment variables:
    *   `AZURE_TENANT_ID`
    *   `AZURE_CLIENT_ID`
    *   `AZURE_CLIENT_SECRET`
    This method is ideal for non-interactive environments like automated scripts or CI/CD pipelines.

3.  **`DefaultAzureCredential`**: This is a powerful credential from the `azure-identity` library that tries multiple authentication mechanisms in sequence, including:
    *   Environment variables (Service Principal).
    *   Managed Identity (when running on Azure services like VMs, App Service, or AKS).
    *   Azure CLI (if the user is logged in via `az login`).
    *   Azure PowerShell.
    *   Interactive browser authentication.
    This is often the best choice for covering a wide range of scenarios.

4.  **`AzureDeveloperCliCredential`**: This method specifically uses the credentials from the **Azure Developer CLI** (`azd`). It is useful for developers who are actively using `azd` for their development workflow.

If all methods fail, the function raises a `ClientAuthenticationError`, clearly indicating that it was unable to authenticate.

#### Usage Example

This function is typically not called directly by application code. Instead, it is used by the factories (e.g., `LLMFactory`, `MemoryFactory`) to obtain the necessary credentials for their respective SDK clients.

```python
# Inside a factory or helper module

from src.factory.utils.utility import _get_azure_credential
from azure.ai.inference.aio import ChatCompletionsClient

def get_inference_client():
    """
    Creates a client for the Azure AI Inference service.
    """
    try:
        # 1. Get the credential using the utility function.
        #    It will automatically figure out the best way to authenticate.
        credential = _get_azure_credential(api_key=config.AZURE_OPENAI_API_KEY)

        # 2. Use the credential to initialize the client.
        client = ChatCompletionsClient(
            endpoint=config.AZURE_AI_INFERENCE_CHAT_ENDPOINT,
            credential=credential
        )
        return client

    except Exception as e:
        print(f"Failed to create client: {e}")
        return None
```

By centralizing this logic, any module that needs to connect to Azure can do so with a single, reliable function call, without having to worry about the complexities of authentication.

---

### `_get_bigquery_client()`

This function initializes a Google BigQuery client with credentials resolved automatically. It standardizes authentication across different environments, ensuring the client is always configured correctly.

### How It Works: Credential Resolution

The function tries the following in order:

1. `BQ_CREDENTIALS_FILE`
If provided in configuration, the client will load service account credentials from a JSON key file.

2. `BQ_CREDENTIALS_JSON`
If provided, the client will parse a JSON string or dictionary containing service account credentials.

3. **Application Default Credentials (ADC)**
If neither file nor JSON credentials are provided, the function falls back to ADC. This allows BigQuery to authenticate automatically when running inside GCP environments like GKE, Cloud Run, or Compute Engine.

#### Usage Example

```python
from src.factory.utils.clients import _get_bigquery_client

def get_bigquery_client():
    """
    Creates a client for the Google BigQuery service.
    """
    try:
        # 1. Get the client using the factory function.
        #    It will automatically resolve authentication in the following order:
        #    - BQ_CREDENTIALS_FILE (service account file path)
        #    - BQ_CREDENTIALS_JSON (JSON string or dict)
        #    - ADC (Application Default Credentials, e.g., GCP runtime)
        client = _get_bigquery_client(
            project_id="", # optional
            location="", # optional
        )

        # 2. Return the ready-to-use client.
        return client

    except Exception as e:
        print(f"Failed to create BigQuery client: {e}")
        return None
```

The function then instantiates a `bigquery.Client` using the resolved credentials, project ID, and location. On success, the client is ready to be used for queries, dataset management, and schema operations.
