# json_provider.py

"""
JSON Memory Provider.

This module implements a JSON file-backed persistent memory provider,
supporting CRUD+Query operations. Useful for prototyping, local development,
or lightweight persistence without external dependencies.

Classes:
    JSONMemoryProvider: JSON-backed implementation of MemoryProviderBase.

Example:
    >>> from factory.memory.json_provider import JSONMemoryProvider
    >>> memory = JSONMemoryProvider("memory.json")
    >>> await memory.upsert("session_123", {"user": "Alice", "context": "hello"})
    >>> result = await memory.get("session_123")
    >>> print(result)
    {"user": "Alice", "context": "hello"}
"""

import uuid
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.factory.memory.base_provider import MemoryProviderBase
from src.factory.logger.telemetry import telemetry


# Get a logger and tracer
logger = telemetry.get_logger(__name__)
tracer = telemetry.get_tracer(__name__)


class JSONMemoryProvider(MemoryProviderBase):
    """Local JSON file-backed persistent memory store.

    Stores all key-value records in a single JSON file. Suitable for
    lightweight persistence in local or test environments.
    """

    def __init__(self, file_path: str = "memory.json") -> None:
        """Initialize the JSON memory provider.

        Creates the file if it does not exist.

        Args:
            file_path (str): Path to the JSON file for storage. Defaults to "memory.json".

        Returns:
            None
        """
        self.file = Path(file_path)
        if not self.file.parent.exists():
            logger.debug("Creating directories for path: %s", self.file.parent)
            self.file.parent.mkdir(parents=True, exist_ok=True)

        if not self.file.exists():
            logger.debug("Creating new JSON memory file: %s", self.file)
            self.file.write_text(json.dumps({}))


    def _read(self) -> Dict[str, Any]:
        """Read all data from the JSON file.

        Returns:
            Dict[str, Any]: Entire JSON file contents.
        """
        logger.debug("Reading JSON memory file: %s", self.file)
        return json.loads(self.file.read_text())

    def _write(self, data: Dict[str, Any]) -> None:
        """Write the given data to the JSON file.

        Args:
            data (Dict[str, Any]): Data to persist.
        """
        logger.debug("Writing data to JSON memory file: %s", self.file)
        self.file.write_text(json.dumps(data, indent=2))

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
        data = self._read()
        logger.debug("Current JSON data keys: %s", list(data.keys()))
        if key in data:
            raise ValueError(f"Key {key} already exists.")

        # Build a new record to avoid mutating the input
        record: Dict[str, Any] = {
            "id": str(uuid.uuid4()),
            **value,
        }

        data[key] = record
        self._write(data)

        return record

    async def upsert(self, key: str, value: Dict[str, Any]) -> Dict[str, Any]:
        """Insert or overwrite a record (idempotent).

        Args:
            key (str): Unique identifier for the record.
            value (Dict[str, Any]): Data to store.

        Returns:
            Dict[str, Any]: The stored record.
        """
        data = self._read()
        data[key] = value
        logger.debug("Upserting item with key: %s", key)
        self._write(data)
        return value

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
        data = self._read()
        if key not in data:
            raise KeyError(f"Key {key} not found.")
        data[key] = value
        logger.debug("Updating item with key: %s", key)
        self._write(data)
        return value

    async def delete(self, key: str) -> None:
        """Delete a record by key.

        Args:
            key (str): Unique identifier for the record.

        Raises:
            KeyError: If the key does not exist.
        """
        data = self._read()
        if key not in data:
            raise KeyError(f"Key {key} not found.")
        data.pop(key)
        logger.debug("Deleted item with key: %s", key)
        self._write(data)

    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve a record by key.

        Args:
            key (str): Unique identifier for the record.

        Returns:
            Optional[Dict[str, Any]]: The stored record, or None if not found.
        """
        data = self._read()
        logger.debug("Current JSON data keys: %s", list(data.keys()))

        data = self._read()
        value = data.get(key)
        if value is None:
            logger.warning("Key %s not found in JSON file.", key)
        else:
            logger.info("Loaded value for key=%s: %s", key, value)

        return value

    async def query(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Retrieve records matching filter criteria.

        Args:
            filters (Dict[str, Any]): Key-value pairs to match.

        Returns:
            List[Dict[str, Any]]: Records matching all filter criteria.
        """
        data = self._read()
        logger.debug("Current JSON data keys: %s", list(data.keys()))
        results = []
        for item in data.values():
            if all(item.get(k) == v for k, v in filters.items()):
                results.append(item)
        return results
