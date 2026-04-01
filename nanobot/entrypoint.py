#!/usr/bin/env python3
"""Entrypoint for nanobot Docker container.

Reads config.json, injects environment variables, writes config.resolved.json,
then launches nanobot gateway.
"""

import json
import os
import sys


def main():
    workspace = os.environ.get("NANOBOT_WORKSPACE", "/app/nanobot/workspace")
    config_path = "/app/nanobot/config.json"
    resolved_path = "/app/nanobot/config.resolved.json"

    with open(config_path, "r") as f:
        config = json.load(f)

    if "providers" in config and "custom" in config["providers"]:
        config["providers"]["custom"]["apiKey"] = os.environ.get("LLM_API_KEY", "")
        config["providers"]["custom"]["apiBase"] = os.environ.get(
            "LLM_API_BASE_URL", ""
        )

    if "agents" in config and "defaults" in config["agents"]:
        config["agents"]["defaults"]["model"] = os.environ.get(
            "LLM_API_MODEL", "coder-model"
        )

    if "gateway" in config:
        config["gateway"]["host"] = os.environ.get(
            "NANOBOT_GATEWAY_CONTAINER_ADDRESS", "0.0.0.0"
        )
        config["gateway"]["port"] = int(
            os.environ.get("NANOBOT_GATEWAY_CONTAINER_PORT", "18790")
        )

    if "tools" in config and "mcpServers" in config["tools"]:
        if "lms" in config["tools"]["mcpServers"]:
            lms_config = config["tools"]["mcpServers"]["lms"]
            lms_config["env"] = {
                "NANOBOT_LMS_BACKEND_URL": os.environ.get(
                    "NANOBOT_LMS_BACKEND_URL", ""
                ),
                "NANOBOT_LMS_API_KEY": os.environ.get("NANOBOT_LMS_API_KEY", ""),
            }
            backend_url = os.environ.get("NANOBOT_LMS_BACKEND_URL", "")
            if backend_url:
                lms_config["args"] = ["-m", "mcp_lms", backend_url]

        if "obs" not in config["tools"]["mcpServers"]:
            config["tools"]["mcpServers"]["obs"] = {}
        obs_config = config["tools"]["mcpServers"]["obs"]
        obs_config["env"] = {
            "NANOBOT_VICTORIALOGS_URL": os.environ.get("NANOBOT_VICTORIALOGS_URL", ""),
            "NANOBOT_VICTORIATRACES_URL": os.environ.get(
                "NANOBOT_VICTORIATRACES_URL", ""
            ),
        }
        obs_config["command"] = "python"
        obs_config["args"] = ["-m", "mcp_obs"]

        config["tools"]["mcpServers"]["webchat"] = {
            "command": "python",
            "args": ["-m", "mcp_webchat"],
            "env": {
                "NANOBOT_WEBCHAT_UI_RELAY_URL": os.environ.get(
                    "NANOBOT_WEBCHAT_UI_RELAY_URL", ""
                ),
                "NANOBOT_WEBCHAT_UI_RELAY_TOKEN": os.environ.get(
                    "NANOBOT_WEBCHAT_UI_RELAY_TOKEN", ""
                ),
            },
        }

    if "channels" not in config:
        config["channels"] = {}
    config["channels"]["webchat"] = {
        "enabled": True,
        "host": os.environ.get("NANOBOT_WEBCHAT_CONTAINER_ADDRESS", "0.0.0.0"),
        "port": int(os.environ.get("NANOBOT_WEBCHAT_CONTAINER_PORT", "18791")),
        "accessKey": os.environ.get("NANOBOT_ACCESS_KEY", ""),
        "allowFrom": ["*"],
    }

    with open(resolved_path, "w") as f:
        json.dump(config, f, indent=2)

    os.execvp(
        "nanobot",
        ["nanobot", "gateway", "--config", resolved_path, "--workspace", workspace],
    )


if __name__ == "__main__":
    main()
