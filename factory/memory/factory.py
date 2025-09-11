"""
LLM Memory Factory

Provides a factory for creating memory provider instances. Supported backends:
Cosmos DB, JSON file, and SQLite.

Usage:
    >>> from factory import MemoryFactory, STORE_COSMOS, STORE_JSON, STORE_SQLITE
    >>> json_store = MemoryFactory.create(STORE_JSON, file_path="memory.json")
    >>> await json_store.save("session1", {"foo": "bar"})
    >>> data = await json_store.load("session1")
    >>> print(data)
    {"foo": "bar"}
"""

from factory.config.app_config import MEMORY_PROVIDERS, DEFAULT_MEMORY_PROVIDER
from factory.memory.base_provider import MemoryProviderBase
from factory.memory.providers.cosmos_provider import CosmosMemoryProvider
from factory.memory.providers.json_provider import JSONMemoryProvider
from factory.logger.telemetry import telemetry


# Get a logger and tracer
logger = telemetry.get_logger(__name__)
tracer = telemetry.get_tracer(__name__)


class MemoryFactory:
    """Factory for creating memory provider instances."""

    def init(
        *,
        endpoint: str = "",
        key: str = "",
        database: str = "",
        container: str = "",
        file_path: str = "memory.json",
        memory_store: str = DEFAULT_MEMORY_PROVIDER,
    ) -> MemoryProviderBase:
        """Create and return a memory provider instance.

        Args:
            memory_store (str, optional): One of {"cosmosdb", "json"}.
                Defaults to DEFAULT_MEMORY_PROVIDER.
            endpoint (str, optional): Cosmos DB endpoint URL (required for cosmosdb).
            key (str, optional): Cosmos DB account key (required for cosmosdb).
            database (str, optional): Cosmos DB database name (required for cosmosdb).
            container (str, optional): Cosmos DB container name (required for cosmosdb).
            file_path (str, optional): Path for JSON memory store.
                Default = "memory.json".

        Returns:
            MemoryProviderBase: An instance of the selected memory provider.

        Raises:
            ValueError: If required arguments are missing or memory_store is invalid.
        """
        memory_store = memory_store.lower()
        logger.debug("Initializing memory provider type=%s", memory_store)

        if memory_store not in MEMORY_PROVIDERS:
            raise ValueError(f"Unsupported memory provider type: {memory_store}")

        if memory_store == "cosmosdb":
            logger.info(
                "Creating Cosmos DB memory provider [db=%s, container=%s]",
                database,
                container,
            )
            return CosmosMemoryProvider(
                endpoint=endpoint,
                key=key,
                database=database,
                container=container,
            )

        if memory_store == "json":
            logger.info("Creating JSON memory provider [file=%s]", file_path)
            return JSONMemoryProvider(file_path=file_path)

        # Defensive catch
        raise ValueError(f"Unsupported memory store: {memory_store}")