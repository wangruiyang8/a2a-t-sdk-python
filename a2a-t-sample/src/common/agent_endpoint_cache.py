from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True, slots=True)
class ResolvedAgentEndpoint:
    agent_name: str
    protocol_binding: str
    protocol_version: str
    url: str


def resolve_preferred_interface(agent_card: dict[str, object]) -> ResolvedAgentEndpoint:
    supported_interfaces = agent_card.get("supportedInterfaces")
    if not isinstance(supported_interfaces, list):
        raise ValueError("AgentCard.supportedInterfaces is required")

    for item in supported_interfaces:
        if not isinstance(item, dict):
            continue

        protocol_binding = str(item.get("protocolBinding", ""))
        url = str(item.get("url", ""))
        if not _is_valid_http_url(url):
            raise ValueError(f"Invalid supportedInterfaces url: {url}")

        return ResolvedAgentEndpoint(
            agent_name=str(agent_card.get("name", "")),
            protocol_binding=protocol_binding,
            protocol_version=str(item.get("protocolVersion", "")),
            url=url,
        )

    raise ValueError("No supported HTTP interface found in AgentCard.supportedInterfaces")


def _is_valid_http_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
