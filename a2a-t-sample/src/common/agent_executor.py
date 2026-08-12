from __future__ import annotations

from a2a.server.agent_execution.agent_executor import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue


class SampleAgentExecutor(AgentExecutor):
    def __init__(
        self,
        *,
        agent_card: object,
        prompt_server: object,
        log_sink: object | None = None,
        debug_enabled: bool = False,
        execute_flow: object,
    ) -> None:
        self._agent_card = agent_card
        self._prompt_server = prompt_server
        self._log_sink = log_sink
        self._debug_enabled = debug_enabled
        self._execute_flow = execute_flow

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        kwargs = {
            "request_context": context,
            "event_queue": event_queue,
            "agent_card": self._agent_card,
            "prompt_server": self._prompt_server,
            "log_sink": self._log_sink,
            "debug_enabled": self._debug_enabled,
        }
        await self._execute_flow(**kwargs)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        return None
