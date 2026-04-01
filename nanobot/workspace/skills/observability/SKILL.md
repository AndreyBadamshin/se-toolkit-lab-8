---
name: observability
description: Use observability MCP tools for logs and traces
always: true
---

# Observability Skill

Use the observability MCP tools (`logs_*`, `traces_*`) to investigate errors and performance issues.

## Available Tools

- `logs_search` — Search VictoriaLogs with a LogsQL query. Returns structured log entries. Parameters: `query`, `limit`.
- `logs_error_count` — Count error-level log entries over a time window, optionally filtered by service. Parameters: `service`, `time_window`.
- `traces_list` — List recent distributed traces for a service from VictoriaTraces. Parameters: `service`, `limit`.
- `traces_get` — Fetch a specific distributed trace by its trace ID. Parameter: `trace_id`.

## When to Use

Use these tools when the user asks about:
- Errors, failures, or issues in the system
- What went wrong with a request
- Performance problems or slow requests
- Any question about system health or debugging

## Investigation Flow for "What went wrong?" or "Check system health"

When the user asks **"What went wrong?"** or **"Check system health"**, follow this investigation flow:

1. **Count recent errors**: Use `logs_error_count` with a fresh time window (e.g., "5m" for 5 minutes) and the most likely failing service (e.g., "Learning Management Service" or "backend").

2. **Search logs**: Use `logs_search` to get the relevant log entries. Include the service name and time window in your query.

3. **Fetch trace**: If the logs contain a `trace_id`, use `traces_get` to fetch the full distributed trace.

4. **Summarize**: Present a concise explanation that mentions:
   - Both log evidence AND trace evidence
   - The affected service
   - The root failing operation
   - Don't dump raw JSON — summarize in plain language

## Examples

**Query**: "Any LMS backend errors in the last 10 minutes?"
```
1. logs_error_count with service="Learning Management Service", time_window="10m"
2. If errors found, logs_search to get details and find trace_id
3. If trace_id found, traces_get to see full trace
4. Summarize the error
```

**Query**: "Why did my request fail?"
```
1. logs_search with query="_time:10m service.name:\"Learning Management Service\" severity:ERROR"
2. Find trace_id from logs
3. traces_get for that trace_id
4. Explain what failed in the trace
```

## Response Style

- Present error summaries in plain language
- Include relevant details (error message, service, timestamp)
- Provide the trace ID when available for further investigation
- If no errors found, say so clearly
