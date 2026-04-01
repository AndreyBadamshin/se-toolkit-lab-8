---
name: lms
description: Use LMS MCP tools for live course data
always: true
---

# LMS Skill

Use the LMS MCP tools (`lms_*`) to fetch live course data from the backend.

## Available Tools

- `lms_health` — Check if the LMS backend is healthy. Returns item count.
- `lms_labs` — List all labs available in the LMS. Use this when you need to let the user choose a lab.
- `lms_learners` — List all learners registered in the LMS.
- `lms_pass_rates` — Get pass rates (avg score and attempt count per task) for a lab. Requires `lab` parameter.
- `lms_timeline` — Get submission timeline (date + submission count) for a lab. Requires `lab` parameter.
- `lms_groups` — Get group performance (avg score + student count per group) for a lab. Requires `lab` parameter.
- `lms_top_learners` — Get top learners by average score for a lab. Requires `lab` parameter, optional `limit` (default 5).
- `lms_completion_rate` — Get completion rate (passed / total) for a lab. Requires `lab` parameter.
- `lms_sync_pipeline` — Trigger the LMS sync pipeline if data appears stale.

## Strategy

- If the user asks for scores, pass rates, completion, groups, timeline, or top learners **without naming a specific lab**, call `lms_labs` first to get available labs.
- When multiple labs are available after calling `lms_labs`, ask the user to choose one before proceeding.
- Use each lab's title as the user-facing label when presenting choices.
- Let the shared `structured-ui` skill decide how to present lab choices on supported channels.
- If the user asks something vague like "show me the scores" or "what's the pass rate?", treat it as a request for lab-specific data and ask which lab they want.

## Response Style

- Format numeric results nicely: show percentages with `%`, counts with proper formatting.
- Keep responses concise — give the data the user asked for without unnecessary preamble.
- If the backend is unhealthy or returns an error, explain the issue clearly.
- When the user asks "what can you do?", explain that you have access to live LMS data including health status, available labs, learner info, pass rates, completion rates, timelines, group performance, and top learners.
