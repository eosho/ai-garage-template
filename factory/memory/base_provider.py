# base_provider.py

"""
Memory Provider Base.

This module defines the abstract base class for persistent memory providers,
which enforces a unified interface for CRUD+Query operations across storage
backends (e.g., Cosmos DB, JSON file storage).

Classes:
    MemoryProviderBase: Abstract base class for persistent memory providers.

Example:
    >>> from factory.memory.json_provider import JSONMemoryProvider
    >>> memory = JSONMemoryProvider("memory.json")
    >>> await memory.create("session_1", {"content": "hello"})
    >>> result = await memory.get("session_1")
    >>> print(result)
    {"content": "hello"}
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class MemoryProviderBase(ABC):
    """Abstract base class for persistent memory providers.

    Provides a universal CRUD+Query interface that can be implemented by
    multiple storage backends (e.g., Cosmos DB, JSON, Redis, SQL).
    """

    @abstractmethod
    async def create(self, key: str, value: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new record. Fails if key already exists.

        Args:
            key (str): Unique identifier for the record.
            value (Dict[str, Any]): Data to store.

        Returns:
            Dict[str, Any]: The stored record.

        Raises:
            ValueError: If the key already exists.
        """
        raise NotImplementedError(
          f"Create method not implemented in {self.__class__.__name__}"
        )

    @abstractmethod
    async def upsert(self, key: str, value: Dict[str, Any]) -> Dict[str, Any]:
        """Insert or overwrite a record (idempotent).

        Args:
            key (str): Unique identifier for the record.
            value (Dict[str, Any]): Data to store.

        Returns:
            Dict[str, Any]: The stored record.
        """
        raise NotImplementedError(
          f"Upsert method not implemented in {self.__class__.__name__}"
        )

    @abstractmethod
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
        raise NotImplementedError(
          f"Update method not implemented in {self.__class__.__name__}"
        )

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete a record by key.

        Args:
            key (str): Unique identifier for the record.

        Raises:
            KeyError: If the key does not exist.
        """
        raise NotImplementedError(
          f"Delete method not implemented in {self.__class__.__name__}"
        )

    @abstractmethod
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve a record by key.

        Args:
            key (str): Unique identifier for the record.

        Returns:
            Optional[Dict[str, Any]]: The stored record or None if not found.
        """
        raise NotImplementedError(
          f"Get method not implemented in {self.__class__.__name__}"
        )

    @abstractmethod
    async def query(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Retrieve records matching filter criteria.

        Args:
            filters (Dict[str, Any]): Key-value filters to match against.

        Returns:
            List[Dict[str, Any]]: List of matching records.
        """
        raise NotImplementedError(
          f"Query method not implemented in {self.__class__.__name__}"
        )
