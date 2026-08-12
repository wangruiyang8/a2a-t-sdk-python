from __future__ import annotations

import asyncio
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import uvicorn
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_rest_routes
from a2a.server.tasks.inmemory_task_store import InMemoryTaskStore
from a2a.utils.constants import TransportProtocol
from a2a_t.server.a2at_server import A2ATServer
from dotenv import dotenv_values
from starlette.applications import Starlette

from common.agent_executor import SampleAgentExecutor
from common.llm_logger import install_llm_logger
from common.logging_utils import build_sample_logger, resolve_sample_debug
from common.registry_client import register_agentcard
from server_example.constants_data import get_public_agent_card
from server_example.server_flow import execute_server_flow

install_llm_logger()

_PROXY_ENV_VAR_NAMES = (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
)


@contextmanager
def _without_proxy_env() -> object:
    original_values = {name: os.environ.get(name) for name in _PROXY_ENV_VAR_NAMES}
    try:
        for name in _PROXY_ENV_VAR_NAMES:
            os.environ.pop(name, None)
        yield
    finally:
        for name, value in original_values.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def build_agent_card_payload(*, host: str, port: int) -> dict[str, Any]:
    card = get_public_agent_card()
    card["supportedInterfaces"] = [
        {
            "protocolBinding": TransportProtocol.HTTP_JSON.value,
            "protocolVersion": "1.0.0",
            "url": f"http://{host}:{port}",
        }
    ]
    return card


def build_registration_payload(*, host: str, port: int) -> dict[str, Any]:
    return {"agentCards": [build_agent_card_payload(host=host, port=port)]}


def build_agent_card(*, host: str, port: int) -> object:
    from a2a.types import AgentCard
    from google.protobuf.json_format import ParseDict
    return ParseDict(build_agent_card_payload(host=host, port=port), AgentCard())


def build_server_runtime(
    *,
    agent_card: object,
    env_path: Path | None = None,
    logger: Any | None = None,
    log_sink: object | None = None,
    debug_enabled: bool = False,
) -> dict[str, object]:
    resolved_logger = logger
    if resolved_logger is None and log_sink is not None and debug_enabled:
        resolved_logger = build_sample_logger(sink=log_sink, debug_enabled=True)
    prompt_server = A2ATServer(env_path=env_path, logger=resolved_logger)
    executor = SampleAgentExecutor(
        agent_card=agent_card,
        prompt_server=prompt_server,
        log_sink=log_sink,
        debug_enabled=debug_enabled,
        execute_flow=execute_server_flow,
    )
    return {
        "prompt_server": prompt_server,
        "executor": executor,
    }


def build_rest_app(
    *,
    agent_card: object,
    executor: object,
) -> object:
    task_store = InMemoryTaskStore()
    request_handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=task_store,
        agent_card=agent_card,
    )
    routes = [
        *create_agent_card_routes(agent_card),
        *create_rest_routes(request_handler),
    ]
    return Starlette(routes=routes)


async def register_agent_card_if_possible(
    *,
    host: str,
    port: int,
    env_path: Path | None = None,
    log_sink: object | None = print,
) -> dict[str, Any]:
    result = await register_agentcard(
        registration_payload=build_registration_payload(host=host, port=port),
        env_path=env_path,
        log_sink=log_sink,
    )
    if log_sink is not None:
        if result.get("status") == "success":
            log_sink("[server] agent-card registration: success")
        else:
            log_sink(
                "[server] agent-card registration failed, continuing startup: "
                f"{result.get('message', 'unknown error')}"
            )
    return result


def resolve_server_bind(*, env_path: Path | None = None) -> tuple[str, int]:
    resolved_env_path = env_path or Path.cwd() / ".env"
    env_values = dotenv_values(resolved_env_path) if resolved_env_path.exists() else {}
    host = str(env_values.get("A2AT_SAMPLE_HOST") or os.environ.get("A2AT_SAMPLE_HOST") or "127.0.0.1")
    port = int(env_values.get("A2AT_SAMPLE_PORT") or os.environ.get("A2AT_SAMPLE_PORT") or "8000")
    return host, port


def main() -> None:
    env_path = Path.cwd() / ".env"
    with _without_proxy_env():
        host, port = resolve_server_bind(env_path=env_path)
        debug_enabled = resolve_sample_debug(env_path=env_path)
        print(f"[server] startup: host={host} port={port} debug={'true' if debug_enabled else 'false'}")
        agent_card = build_agent_card(host=host, port=port)
        asyncio.run(
            register_agent_card_if_possible(
                host=host,
                port=port,
                env_path=env_path if env_path.exists() else None,
                log_sink=print,
            )
        )
        runtime = build_server_runtime(
            agent_card=agent_card,
            env_path=env_path if env_path.exists() else None,
            log_sink=print,
            debug_enabled=debug_enabled,
        )
        app = build_rest_app(
            agent_card=agent_card,
            executor=runtime["executor"],
        )
        uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
