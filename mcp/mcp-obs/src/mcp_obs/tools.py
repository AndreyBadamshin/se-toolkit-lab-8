"""Tool schemas, handlers, and registry for the observability MCP server."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from mcp.types import Tool
from pydantic import BaseModel, Field

from mcp_obs.client import ObsClient


class NoArgs(BaseModel):
    """Empty input model for tools that only need server-side configuration."""


class LogsSearchQuery(BaseModel):
    query: str = Field(
        description="LogsQL query string. Examples: '_time:10m severity:ERROR' or 'service.name:\"Learning Management Service\" severity:ERROR'"
    )
    limit: int = Field(default=50, ge=1, le=500, description="Max entries to return.")


class LogsErrorCountQuery(BaseModel):
    service: str | None = Field(
        default=None,
        description="Service name to filter by, e.g. 'Learning Management Service'",
    )
    time_window: str = Field(
        default="1h",
        description="Time window for the query, e.g. '10m', '1h', '24h'",
    )


class TracesListQuery(BaseModel):
    service: str = Field(description="Service name to list traces for.")
    limit: int = Field(default=20, ge=1, le=100, description="Max traces to return.")


class TracesGetQuery(BaseModel):
    trace_id: str = Field(description="The trace ID to fetch.")


ToolPayload = Any
ToolHandler = Callable[[ObsClient, BaseModel], Awaitable[ToolPayload]]


@dataclass(frozen=True, slots=True)
class ToolSpec:
    name: str
    description: str
    model: type[BaseModel]
    handler: ToolHandler

    def as_tool(self) -> Tool:
        schema = self.model.model_json_schema()
        schema.pop("$defs", None)
        schema.pop("title", None)
        return Tool(name=self.name, description=self.description, inputSchema=schema)


async def _logs_search(client: ObsClient, args: BaseModel) -> ToolPayload:
    query = _require_logs_search_query(args)
    return await client.logs_search(query.query, limit=query.limit)


async def _logs_error_count(client: ObsClient, args: BaseModel) -> ToolPayload:
    query = _require_logs_error_count_query(args)
    return await client.logs_error_count(query.service, query.time_window)


async def _traces_list(client: ObsClient, args: BaseModel) -> ToolPayload:
    query = _require_traces_list_query(args)
    return await client.traces_list(query.service, limit=query.limit)


async def _traces_get(client: ObsClient, args: BaseModel) -> ToolPayload:
    query = _require_traces_get_query(args)
    return await client.traces_get(query.trace_id)


def _require_logs_search_query(args: BaseModel) -> LogsSearchQuery:
    if not isinstance(args, LogsSearchQuery):
        raise TypeError(
            f"Expected {LogsSearchQuery.__name__}, got {type(args).__name__}"
        )
    return args


def _require_logs_error_count_query(args: BaseModel) -> LogsErrorCountQuery:
    if not isinstance(args, LogsErrorCountQuery):
        raise TypeError(
            f"Expected {LogsErrorCountQuery.__name__}, got {type(args).__name__}"
        )
    return args


def _require_traces_list_query(args: BaseModel) -> TracesListQuery:
    if not isinstance(args, TracesListQuery):
        raise TypeError(
            f"Expected {TracesListQuery.__name__}, got {type(args).__name__}"
        )
    return args


def _require_traces_get_query(args: BaseModel) -> TracesGetQuery:
    if not isinstance(args, TracesGetQuery):
        raise TypeError(
            f"Expected {TracesGetQuery.__name__}, got {type(args).__name__}"
        )
    return args


TOOL_SPECS = (
    ToolSpec(
        "logs_search",
        "Search VictoriaLogs with a LogsQL query. Returns structured log entries.",
        LogsSearchQuery,
        _logs_search,
    ),
    ToolSpec(
        "logs_error_count",
        "Count error-level log entries over a time window, optionally filtered by service.",
        LogsErrorCountQuery,
        _logs_error_count,
    ),
    ToolSpec(
        "traces_list",
        "List recent distributed traces for a service from VictoriaTraces.",
        TracesListQuery,
        _traces_list,
    ),
    ToolSpec(
        "traces_get",
        "Fetch a specific distributed trace by its trace ID.",
        TracesGetQuery,
        _traces_get,
    ),
)
TOOLS_BY_NAME = {spec.name: spec for spec in TOOL_SPECS}
