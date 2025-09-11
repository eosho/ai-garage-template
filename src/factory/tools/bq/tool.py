# tool.py

"""
BigQuery Tool.

Provides async-friendly wrappers around the synchronous Google BigQuery SDK.
It is intended for use in agent orchestration frameworks (e.g., LangChain,
LangGraph, Semantic Kernel) where the agent may need to query BigQuery or
inspect schemas as part of its reasoning process.

Features:
    * Uses a BigQuery client initialized in utils.py via app_config.py:
        - BQ_CREDENTIALS_FILE → path to service account key file
        - BQ_CREDENTIALS_JSON → JSON string or dict of service account creds
        - Falls back to Application Default Credentials (ADC) if neither is set
    * Executes parameterized queries with safe type inference.
    * Fetches table schemas for validation or planning.

Intended Usage:
    Register these functions as tools in your agent supervisor so queries can
    be executed safely as part of workflows, without exposing the BigQuery SDK.

Example:
    >>> from src.factory.tools.bq import run_query, get_schema
    >>> result = await run_query("SELECT * FROM `dataset.table` WHERE id=@id",
    ...                          params={"id": 123})
    >>> print(result["rows"][0])
    ...
    >>> schema = await get_schema("my_dataset", "users")
    >>> print(schema)
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional, Set, Callable

from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError

from src.factory.logger.telemetry import telemetry
from factory.utils.clients import _get_bigquery_client


# Telemetry
logger = telemetry.get_logger(__name__)
tracer = telemetry.get_tracer(__name__)

# Initialize client once
_client = _get_bigquery_client()


async def run_query(
    query: str,
    params: Optional[Dict[str, Any]] = None,
    timeout: int = 60,
) -> Dict[str, Any]:
    """
    Execute a SQL query and return rows with metadata.

    Args:
        query: SQL query string (use @name for named parameters).
        params: Mapping of parameter names to Python values. Supported types:
            - bool → BOOL
            - int → INT64
            - float → FLOAT64
            - other → STRING
        timeout: Max query runtime in seconds (default: 60).

    Returns:
        Dict with:
            - "rows": List[Dict[str, Any]] — rows as dicts
            - "metadata": job_id, total_rows, project

    Raises:
        Exception: On query execution failure.
    """
    return await asyncio.to_thread(_execute_query, query, params, timeout)


async def get_schema(dataset: str, table: str) -> List[Dict[str, Any]]:
    """
    Fetch schema for a BigQuery table.

    Args:
        dataset: Dataset ID.
        table: Table ID.

    Returns:
        List of {"name": str, "type": str, "mode": str} entries.

    Raises:
        Exception: On schema fetch failure.
    """
    return await asyncio.to_thread(_fetch_schema, dataset, table)


# ---------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------

def _execute_query(
    query: str,
    params: Optional[Dict[str, Any]],
    timeout: int,
) -> Dict[str, Any]:
    """Blocking query execution helper (wrapped in to_thread).

    Args:
        query: SQL query string (use @name for named parameters).
        params: Mapping of parameter names to Python values.
        timeout: Max query runtime in seconds (default: 60).

    Returns:
        Dict[str, Any]: Query execution result including rows and metadata.
    """
    job_config = _make_job_config(params)
    try:
        job = _client.query(query, job_config=job_config, timeout=timeout)
        result = job.result()
        rows = [dict(row.items()) for row in result]
        return {
            "rows": rows,
            "metadata": {
                "job_id": job.job_id,
                "total_rows": result.total_rows,
                "project": _client.project,
            },
        }
    except GoogleCloudError as gce:
        raise Exception(f"BigQuery API error: {gce}") from gce
    except Exception as exc:
        raise Exception(f"Query execution failed: {exc}") from exc


def _fetch_schema(dataset: str, table: str) -> List[Dict[str, Any]]:
    """Blocking schema fetch helper (wrapped in to_thread).

    Args:
        dataset: Dataset ID.
        table: Table ID.

    Returns:
        List[Dict[str, Any]]: Table schema information.
    """
    try:
        table_ref = _client.dataset(dataset).table(table)
        table_obj = _client.get_table(table_ref)
        return [
            {"name": f.name, "type": f.field_type, "mode": f.mode}
            for f in table_obj.schema
        ]
    except Exception as exc:
        raise Exception(f"Failed to fetch schema: {exc}") from exc


def _make_job_config(params: Optional[Dict[str, Any]]) -> bigquery.QueryJobConfig:
    """Create a BigQuery job config with typed query parameters.

    Args:
        params: Mapping of parameter names to Python values.

    Returns:
        bigquery.QueryJobConfig: Configured job config with parameters.
    """
    job_config = bigquery.QueryJobConfig()
    if params:
        job_config.query_parameters = [
            bigquery.ScalarQueryParameter(name, _infer_type(value), value)
            for name, value in params.items()
        ]
    return job_config

def _infer_type(value: Any) -> str:
    """Infer BigQuery parameter type from a Python value.

    Args:
        value: Python value to infer type from.
    """
    if isinstance(value, bool):
        return "BOOL"
    if isinstance(value, int):
        return "INT64"
    if isinstance(value, float):
        return "FLOAT64"
    return "STRING"


# Statically defined utility functions for fast reference
bq_tools: Set[Callable[..., Any]] = {
    run_query,
    get_schema,
}