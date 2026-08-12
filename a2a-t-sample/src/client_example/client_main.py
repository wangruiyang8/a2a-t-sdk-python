from __future__ import annotations

import asyncio
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from a2a.client.client import ClientConfig
from a2a.client.client_factory import ClientFactory
from a2a.types import AgentCard
from a2a.utils.constants import TransportProtocol
from dotenv import dotenv_values
from google.protobuf.json_format import ParseDict

from client_example.client_bootstrap import build_client_runtime
from client_example.client_flow import run_client_flow
from client_example.scenario_data import build_subscription_request
from common.agent_endpoint_cache import resolve_preferred_interface
from common.llm_logger import install_llm_logger
from common.logging_utils import build_sample_logger, resolve_sample_debug
from common.registry_client import query_by_name_org

install_llm_logger(verbose=False)

_PROXY_ENV_VAR_NAMES = (
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
)


def resolve_server_url(*, env_path: Path | None = None) -> str:
    resolved_env_path = env_path or Path.cwd() / ".env"
    env_values = dotenv_values(resolved_env_path) if resolved_env_path.exists() else {}
    host = str(env_values.get("A2AT_SAMPLE_HOST") or os.environ.get("A2AT_SAMPLE_HOST") or "127.0.0.1")
    port = int(env_values.get("A2AT_SAMPLE_PORT") or os.environ.get("A2AT_SAMPLE_PORT") or "8000")
    return f"http://{host}:{port}"


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


async def run_main(
    *,
    env_path: Path | None,
    initial_input: dict[str, object],
    bootstrap: object = build_client_runtime,
    flow: object = run_client_flow,
    logger: Any | None = None,
    log_sink: object | None = None,
    debug_enabled: bool = False,
    max_artifacts: int | None = None,
    registry_query_fn: object = query_by_name_org,
) -> object:
    resolved_logger = logger
    if resolved_logger is None and log_sink is not None and debug_enabled:
        resolved_logger = build_sample_logger(sink=log_sink, debug_enabled=True)
    runtime = await bootstrap(env_path=env_path, logger=resolved_logger)

    agent_card_query = initial_input.get("agent_card_query")
    query_name = str(agent_card_query.get("name", "")) if isinstance(agent_card_query, dict) else ""
    query_org = str(agent_card_query.get("organization", "")) if isinstance(agent_card_query, dict) else ""
    agent_card_response = await registry_query_fn(
        organization=query_org,
        name=query_name,
        env_path=env_path,
        log_sink=log_sink,
    )
    agent_card_dict = agent_card_response["agentCards"][0]
    endpoint = resolve_preferred_interface(agent_card_dict)
    if log_sink is not None:
        log_sink(f"[client] agent-discovered: url={endpoint.url} binding={endpoint.protocol_binding}")

    client_factory = ClientFactory(
        ClientConfig(
            httpx_client=runtime["httpx_client"],
            supported_protocol_bindings=[TransportProtocol.HTTP_JSON],
            use_client_preference=True,
        )
    )
    agent_card = ParseDict(agent_card_dict, AgentCard())
    a2a_client = client_factory.create(agent_card)

    if log_sink is not None:
        log_sink(f"[client] bootstrap-ready: server_url={endpoint.url}")
    return await flow(
        prompt_client=runtime["prompt_client"],
        a2a_client=a2a_client,
        initial_input=initial_input,
        max_artifacts=max_artifacts,
        log_sink=log_sink,
    )


def main(
    *,
    env_path: Path | None = None,
    run_async: object = run_main,
    async_runner: object = asyncio.run,
) -> object:
    resolved_env_path = env_path or Path.cwd() / ".env"
    with _without_proxy_env():
        debug_enabled = resolve_sample_debug(env_path=resolved_env_path)
        print(
            f"[client] startup: server_url={resolve_server_url(env_path=resolved_env_path)} "
            f"debug={'true' if debug_enabled else 'false'}"
        )
        return async_runner(
            run_async(
                env_path=resolved_env_path if resolved_env_path.exists() else None,
                initial_input=build_subscription_request(),
                log_sink=print,
                debug_enabled=debug_enabled,
            )
        )


if __name__ == "__main__":
    main()
