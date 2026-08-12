from __future__ import annotations

import json
from typing import Any

from a2a_t.llm.providers.openai import OpenAIClient

_original_build_payload = OpenAIClient._build_structured_payload
_original_structured = OpenAIClient.structured


def _patched_build_payload_verbose(
    self: OpenAIClient,
    *,
    messages: list[dict[str, str]],
    json_schema: dict[str, Any],
    temperature: float | None,
    max_tokens: int | None,
) -> dict[str, Any]:
    payload = _original_build_payload(
        self,
        messages=messages,
        json_schema=json_schema,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    print(f"[llm] request payload to {self._config.base_url}:")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return payload


def _patched_structured_verbose(
    self: OpenAIClient,
    *,
    messages: list[dict[str, str]],
    json_schema: dict[str, Any],
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> Any:
    result = _original_structured(
        self,
        messages=messages,
        json_schema=json_schema,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    print(f"[llm] response content: {result.content}")
    print(f"[llm] response model: {result.model}")
    print(f"[llm] response usage: {result.usage}")
    return result


def _patched_build_payload_brief(
    self: OpenAIClient,
    *,
    messages: list[dict[str, str]],
    json_schema: dict[str, Any],
    temperature: float | None,
    max_tokens: int | None,
) -> dict[str, Any]:
    payload = _original_build_payload(
        self,
        messages=messages,
        json_schema=json_schema,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    print(f"[llm] request: model={payload.get('model', '?')} messages={len(payload.get('messages', []))}")
    return payload


def _patched_structured_brief(
    self: OpenAIClient,
    *,
    messages: list[dict[str, str]],
    json_schema: dict[str, Any],
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> Any:
    result = _original_structured(
        self,
        messages=messages,
        json_schema=json_schema,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    usage = result.usage or {}
    print(f"[llm] response: model={result.model} usage={dict(usage)}")
    return result


def install_llm_logger(*, verbose: bool = True) -> None:
    if verbose:
        OpenAIClient._build_structured_payload = _patched_build_payload_verbose
        OpenAIClient.structured = _patched_structured_verbose
    else:
        OpenAIClient._build_structured_payload = _patched_build_payload_brief
        OpenAIClient.structured = _patched_structured_brief
