from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = PROJECT_ROOT / "a2a-t-sample" / "src"
TEST_ROOT = PROJECT_ROOT / "a2a-t-sample" / "test"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
if str(TEST_ROOT) not in sys.path:
    sys.path.append(str(TEST_ROOT))

from a2a.server.agent_execution.context import RequestContext
from a2a.types import Message, Role, TaskArtifactUpdateEvent, TaskState, TaskStatusUpdateEvent
from support import FakeEventQueue, FakePromptServer

from server_example.server_flow import execute_server_flow


def _make_request_context(text: str = "test prompt") -> RequestContext:
    message = Message()
    message.message_id = "msg-1"
    message.role = Role.ROLE_USER
    message.parts.add().text = text

    class FakeRequestContext:
        def __init__(self, msg: object) -> None:
            self.message = msg
            self.current_task = None
            self.task_id = "task-1"
            self.context_id = "ctx-1"
            class FakeCallContext:
                state: dict = {}
            self.call_context = FakeCallContext()

    return FakeRequestContext(message)


def _make_fake_agent_card(streaming: bool = True) -> object:
    class FakeAgentCard:
        def __init__(self) -> None:
            class FakeCapabilities:
                extensions = []
            FakeCapabilities.streaming = streaming
            self.capabilities = FakeCapabilities()
    return FakeAgentCard()


class ExecuteServerFlowTest(unittest.IsolatedAsyncioTestCase):
    async def test_valid_prompt_pushes_artifacts_and_completes(self) -> None:
        prompt_server = FakePromptServer(check_success=True)
        event_queue = FakeEventQueue()
        request_context = _make_request_context("complete prompt")
        agent_card = _make_fake_agent_card()

        async def fake_sleep(seconds: float) -> None:
            pass

        await execute_server_flow(
            request_context=request_context,
            event_queue=event_queue,
            agent_card=agent_card,
            prompt_server=prompt_server,
            max_artifacts=3,
            sleep_fn=fake_sleep,
        )

        artifact_count = sum(1 for e in event_queue.events if isinstance(e, TaskArtifactUpdateEvent))
        status_events = [e for e in event_queue.events if isinstance(e, TaskStatusUpdateEvent)]

        self.assertEqual(artifact_count, 3)
        self.assertGreaterEqual(len(status_events), 2)
        completed_states = [e for e in status_events if e.status.state == TaskState.TASK_STATE_COMPLETED]
        self.assertEqual(len(completed_states), 1)

    async def test_prompt_check_failure_raises(self) -> None:
        prompt_server = FakePromptServer(check_success=False)
        event_queue = FakeEventQueue()
        request_context = _make_request_context("bad prompt")
        agent_card = _make_fake_agent_card()

        with self.assertRaises(RuntimeError):
            await execute_server_flow(
                request_context=request_context,
                event_queue=event_queue,
                agent_card=agent_card,
                prompt_server=prompt_server,
                max_artifacts=1,
            )

    async def test_max_artifacts_none_means_infinite_but_test_cuts_short(self) -> None:
        prompt_server = FakePromptServer(check_success=True)
        event_queue = FakeEventQueue()
        request_context = _make_request_context("complete prompt")
        agent_card = _make_fake_agent_card()

        call_count = 0

        async def counting_sleep(seconds: float) -> None:
            nonlocal call_count
            call_count += 1
            if call_count >= 5:
                raise InterruptedError("stop")

        with self.assertRaises(InterruptedError):
            await execute_server_flow(
                request_context=request_context,
                event_queue=event_queue,
                agent_card=agent_card,
                prompt_server=prompt_server,
                max_artifacts=None,
                sleep_fn=counting_sleep,
            )

        artifact_count = sum(1 for e in event_queue.events if isinstance(e, TaskArtifactUpdateEvent))
        self.assertGreaterEqual(artifact_count, 4)


if __name__ == "__main__":
    unittest.main()
