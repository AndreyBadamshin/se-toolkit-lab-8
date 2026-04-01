"""Runtime settings for the observability MCP server."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    victorialogs_url: str
    victoriatraces_url: str


def resolve_victorialogs_url() -> str:
    value = os.environ.get("NANOBOT_VICTORIALOGS_URL", "").strip()
    if not value:
        raise RuntimeError(
            "VictoriaLogs URL not configured. Set NANOBOT_VICTORIALOGS_URL."
        )
    return value


def resolve_victoriatraces_url() -> str:
    value = os.environ.get("NANOBOT_VICTORIATRACES_URL", "").strip()
    if not value:
        raise RuntimeError(
            "VictoriaTraces URL not configured. Set NANOBOT_VICTORIATRACES_URL."
        )
    return value


def resolve_settings() -> Settings:
    return Settings(
        victorialogs_url=resolve_victorialogs_url(),
        victoriatraces_url=resolve_victoriatraces_url(),
    )
