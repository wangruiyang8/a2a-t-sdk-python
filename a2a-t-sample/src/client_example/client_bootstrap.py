from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx
from a2a_t.client.a2at_client import A2ATClient
from dotenv import dotenv_values


def _resolve_http_timeout_seconds(*, env_path: Path | None = None) -> float:
    resolved_env_path = env_path or Path.cwd() / ".env"
    env_values = dotenv_values(resolved_env_path) if resolved_env_path.exists() else {}
    raw_timeout = env_values.get("A2AT_LLM_TIMEOUT_SECONDS")
    if raw_timeout is None:
        return 60.0
    return float(raw_timeout)


async def build_client_runtime(
    *,
    env_path: Path | None = None,
    logger: Any | None = None,
    prompt_client_cls: type = A2ATClient,
) -> dict[str, object]:
    httpx_client = httpx.AsyncClient(
        timeout=_resolve_http_timeout_seconds(env_path=env_path),
        trust_env=False,
    )
    prompt_client = prompt_client_cls(env_path=env_path, logger=logger)
    return {
        "prompt_client": prompt_client,
        "httpx_client": httpx_client,
    }
