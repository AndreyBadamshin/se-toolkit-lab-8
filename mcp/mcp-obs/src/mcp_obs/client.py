"""Async HTTP client for VictoriaLogs and VictoriaTraces APIs."""

from __future__ import annotations

import json
from typing import Any

import httpx
from pydantic import BaseModel


class LogEntry(BaseModel):
    timestamp: str
    level: str
    service: str
    event: str
    message: str
    trace_id: str | None = None


class TraceSummary(BaseModel):
    trace_id: str
    service_name: str
    duration_ms: float
    start_time: str
    span_count: int = 0


class TraceDetail(BaseModel):
    trace_id: str
    service_name: str
    duration_ms: float
    start_time: str
    spans: list[dict[str, Any]] = []


class ObsClient:
    """Client for VictoriaLogs and VictoriaTraces."""

    def __init__(
        self,
        victorialogs_url: str,
        victoriatraces_url: str,
        *,
        http_client: httpx.AsyncClient | None = None,
        timeout: float = 10.0,
    ) -> None:
        self.victorialogs_url = victorialogs_url.rstrip("/")
        self.victoriatraces_url = victoriatraces_url.rstrip("/")
        self._owns_client = http_client is None
        self._http_client = http_client or httpx.AsyncClient(timeout=timeout)

    async def __aenter__(self) -> ObsClient:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._owns_client:
            await self._http_client.aclose()

    async def _get(self, url: str, params: dict[str, Any] | None = None) -> Any:
        response = await self._http_client.get(url, params=params)
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        if "stream" in content_type or "application/x-ndjson" in content_type:
            lines = response.text.strip().split("\n")
            return [json.loads(line) for line in lines if line.strip()]
        return response.json()

    async def _post(self, url: str, data: dict[str, Any] | None = None) -> Any:
        response = await self._http_client.post(url, json=data)
        response.raise_for_status()
        return response.json()

    async def logs_search(
        self,
        query: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Search VictoriaLogs with a LogsQL query."""
        params: dict[str, Any] = {"query": query, "limit": limit}
        url = f"{self.victorialogs_url}/select/logsql/query"
        result = await self._get(url, params)
        if isinstance(result, list):
            return result[:limit] if limit else result
        if isinstance(result, dict):
            data = result.get("data", [])
            if isinstance(data, list):
                return data[:limit] if limit else data
        return []

    async def logs_error_count(
        self,
        service: str | None = None,
        time_window: str = "1h",
    ) -> dict[str, Any]:
        """Count error logs over a time window."""
        query_parts = [f"_time:{time_window}"]
        if service:
            query_parts.append(f'service.name:"{service}"')
        query_parts.append("severity:ERROR")
        query_str = " ".join(query_parts)

        params: dict[str, Any] = {"query": query_str, "limit": 0}
        url = f"{self.victorialogs_url}/select/logsql/query"
        result = await self._get(url, params)

        total = 0
        if isinstance(result, dict):
            total_val = result.get("_total", 0)
            total = int(total_val) if total_val else 0
        elif isinstance(result, list):
            total = len(result)

        return {"error_count": total, "query": query_str}

    async def traces_list(
        self,
        service: str,
        limit: int = 20,
    ) -> list[TraceSummary]:
        """List recent traces for a service."""
        params: dict[str, Any] = {"service": service, "limit": limit}
        url = f"{self.victoriatraces_url}/select/jaeger/api/traces"
        result = await self._get(url, params)

        traces: list[TraceSummary] = []
        if isinstance(result, dict):
            data = result.get("data", [])
            if isinstance(data, list):
                for item in data:
                    if not isinstance(item, dict):
                        continue
                    spans: list[dict[str, Any]] = item.get("spans", [])
                    start_time = str(item.get("startTimeUnixNano", "0"))
                    duration = float(item.get("duration", 0)) / 1_000_000
                    trace_service = ""
                    for span in spans:
                        if isinstance(span, dict):
                            process = span.get("process", {})
                            if isinstance(process, dict) and process.get("serviceName"):
                                trace_service = str(process["serviceName"])
                                break

                    traces.append(
                        TraceSummary(
                            trace_id=str(item.get("traceID", "")),
                            service_name=trace_service,
                            duration_ms=duration,
                            start_time=start_time,
                            span_count=len(spans),
                        )
                    )

        return traces

    async def traces_get(self, trace_id: str) -> TraceDetail | None:
        """Fetch a specific trace by ID."""
        url = f"{self.victoriatraces_url}/select/jaeger/api/traces/{trace_id}"
        result = await self._get(url)

        if isinstance(result, dict):
            data = result.get("data", [])
            if isinstance(data, list) and data:
                item = data[0]
                if not isinstance(item, dict):
                    return None
                spans: list[dict[str, Any]] = item.get("spans", [])
                start_time = str(item.get("startTimeUnixNano", "0"))
                duration = float(item.get("duration", 0)) / 1_000_000

                trace_service = ""
                for span in spans:
                    if isinstance(span, dict):
                        process = span.get("process", {})
                        if isinstance(process, dict) and process.get("serviceName"):
                            trace_service = str(process["serviceName"])
                            break

                return TraceDetail(
                    trace_id=str(item.get("traceID", "")),
                    service_name=trace_service,
                    duration_ms=duration,
                    start_time=start_time,
                    spans=spans,
                )

        return None
