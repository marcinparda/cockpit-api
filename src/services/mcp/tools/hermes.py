import os
from typing import Any

import yaml
from mcp.server.fastmcp import FastMCP

HERMES_CONFIG_PATH = os.getenv("HERMES_CONFIG_PATH", "/opt/hermes/config.yaml")
HERMES_CONTAINER_NAME = os.getenv("HERMES_CONTAINER_NAME", "hermes")


def _read_config() -> dict:
    if not os.path.exists(HERMES_CONFIG_PATH):
        return {}
    with open(HERMES_CONFIG_PATH) as f:
        return yaml.safe_load(f) or {}


def _write_config(config: dict) -> None:
    os.makedirs(os.path.dirname(HERMES_CONFIG_PATH), exist_ok=True)
    with open(HERMES_CONFIG_PATH, "w") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)


def _restart_hermes() -> None:
    import docker
    client = docker.from_env()
    client.containers.get(HERMES_CONTAINER_NAME).restart()


def register_hermes_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    async def hermes_get_model() -> Any:
        """Get the current default model configured for the Hermes agent."""
        config = _read_config()
        model = config.get("model", {}).get("default", "not set")
        return {"model": model, "config_path": HERMES_CONFIG_PATH}

    @mcp.tool()
    async def hermes_set_model(model: str) -> Any:
        """Set the default model for the Hermes agent and restart it.

        Args:
            model: OpenRouter model ID, e.g. 'openai/gpt-5-mini', 'meta-llama/llama-3.3-70b-instruct:free'
        """
        config = _read_config()
        if "model" not in config:
            config["model"] = {}
        config["model"]["default"] = model
        config["model"]["provider"] = "auto"
        config["model"]["base_url"] = "https://openrouter.ai/api/v1"
        _write_config(config)
        _restart_hermes()
        return {"model": model, "status": "updated and restarted"}
