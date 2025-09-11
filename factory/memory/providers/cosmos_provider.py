# cosmos_provider.py
"""
CosmosDB Memory Provider.

This module implements a Cosmos DB-backed persistent memory provider,
supporting CRUD+Query operations with partition key on `id`.

Classes:
    CosmosMemoryProvider: Cosmos DB-backed implementation of MemoryProviderBase.

Example:
    >>> from factory.memory.cosmos_provider import CosmosMemoryProvider
    >>>
    >>> provider = CosmosMemoryProvider(
    ...     endpoint="https://<cosmos-account>.documents.azure.com:443/",
    ...     key="<your-key>",
    ...     database="llm-memory",
    ...     container="sessions",
    ... )
    >>> await provider.upsert("session_123", {"user": "Bob", "context": "hazard"})
    >>> result = await provider.get("session_123")
    >>> print(result)
    {"id": "session_123", "user": "Bob", "context": "hazard"}
"""

from typing import Any, Dict, List, Optional
from azure.cosmos.aio import CosmosClient
from azure.cosmos import PartitionKey, exceptions

from src.factory.memory.base_provider import MemoryProviderBase
from factory.utils.clients import _get_azure_credential
from src.factory.logger.telemetry import telemetry


# Get a logger and tracer
logger = telemetry.get_logger(__name__)
tracer = telemetry.get_tracer(__name__)



class CosmosMemoryProvider(MemoryProviderBase):
    """Azure Cosmos DB-backed persistent memory store."""

    def __init__(self, endpoint: str, key: Optional[str], database: str, container: str) -> None:
        """Initialize Cosmos DB memory provider.

        Args:
            endpoint (str): Cosmos DB endpoint URL.
            key (str): Primary or secondary key for Cosmos DB account.
            database (str): Name of the target database.
            container (str): Name of the container.
        """
        credential = _get_azure_credential(api_key=key if key is not None else "")
        self.client = CosmosClient(endpoint, credential=credential)
        self.database_name = database
        self.container_name = container

    async def _get_container(self):
        """Get or create Cosmos DB container."""
        db = await self.client.create_database_if_not_exists(id=self.database_name)
        container = await db.create_container_if_not_exists(
            id=self.container_name,
            partition_key=PartitionKey(path="/id"),
        )
        logger.debug("Initialized Cosmos DB container: %s/%s", self.database_name, self.container_name)
        return container

    async def create(self, key: str, value: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new record. Fails if the key already exists.

        Args:
            key (str): Unique identifier for the record.
            value (Dict[str, Any]): Data to store.

        Returns:
            Dict[str, Any]: The stored record.

        Raises:
            ValueError: If the key already exists.
        """
        container = await self._get_container()
        value["id"] = key
        logger.debug("Creating item with key: %s", key)
        try:
            return await container.create_item(body=value)
        except exceptions.CosmosResourceExistsError:
            raise ValueError(f"Key {key} already exists.")

    async def upsert(self, key: str, value: Dict[str, Any]) -> Dict[str, Any]:
        """Insert or overwrite a record (idempotent).

        Args:
            key (str): Unique identifier for the record.
            value (Dict[str, Any]): Data to store.

        Returns:
            Dict[str, Any]: The stored record.
        """
        container = await self._get_container()
        value["id"] = key
        logger.debug("Upserting item with key: %s", key)
        return await container.upsert_item(body=value)

    async def update(self, key: str, value: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing record. Fails if not found.

        Args:
            key (str): Unique identifier for the record.
            value (Dict[str, Any]): Updated data.

        Returns:
            Dict[str, Any]: The updated record.

        Raises:
            KeyError: If the key does not exist.
        """
        container = await self._get_container()
        try:
            existing = await container.read_item(item=key, partition_key=key)
        except exceptions.CosmosResourceNotFoundError:
            raise KeyError(f"Key {key} not found.")
        value["id"] = key
        logger.debug("Updating item with key: %s", key)
        return await container.replace_item(item=existing, body=value)

    async def delete(self, key: str) -> None:
        """Delete a record by key.

        Args:
            key (str): Unique identifier for the record.

        Raises:
            KeyError: If the key does not exist.
        """
        container = await self._get_container()
        try:
            await container.delete_item(item=key, partition_key=key)
            logger.debug("Deleted item with key: %s", key)
        except exceptions.CosmosResourceNotFoundError:
            raise KeyError(f"Key {key} not found.")

    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve a record by key.

        Args:
            key (str): Unique identifier for the record.

        Returns:
            Optional[Dict[str, Any]]: The stored record, or None if not found.
        """
        container = await self._get_container()
        try:
            logger.debug("Reading item with key: %s", key)
            return await container.read_item(item=key, partition_key=key)
        except exceptions.CosmosResourceNotFoundError:
            return None

    async def query(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Retrieve records matching filter criteria.

        Args:
            filters (Dict[str, Any]): Key-value pairs to match.

        Returns:
            List[Dict[str, Any]]: Records matching the filter criteria.
        """
        container = await self._get_container()
        clauses = " AND ".join([f"c.{k}=@{k}" for k in filters.keys()])
        query = f"SELECT * FROM c WHERE {clauses}" if clauses else "SELECT * FROM c"
        params = [{"name": f"@{k}", "value": v} for k, v in filters.items()]

        logger.debug("Querying items with params: %s", params)
        results = [item async for item in container.query_items(query=query, parameters=params)]
        return results
