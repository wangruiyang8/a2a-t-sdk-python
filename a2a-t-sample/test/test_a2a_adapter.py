from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "a2a-t-sample" / "src"
TEST_ROOT = PROJECT_ROOT / "a2a-t-sample" / "test"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))
if str(TEST_ROOT) not in sys.path:
    sys.path.append(str(TEST_ROOT))

from a2a.types import Message, Role
from support import FakeEventQueue

from common.a2a_adapter import (
    build_artifact,
    build_status,
    build_status_message,
    emit_status_update,
    extract_request_payload,
)


class ExtractRequestPayloadTest(unittest.TestCase):
    def test_extracts_text_from_message(self) -> None:
        message = Message()
        message.message_id = "msg-1"
        message.role = Role.ROLE_USER
        message.parts.add().text = "subscribe to incidents"

        payload = extract_request_payload(message)

        self.assertEqual(payload["text"], "subscribe to incidents")

    def test_extracts_text_from_send_message_request(self) -> None:
        from a2a.types import SendMessageRequest
        request = SendMessageRequest()
        request.message.message_id = "msg-2"
        request.message.role = Role.ROLE_USER
        request.message.parts.add().text = "hello"

        payload = extract_request_payload(request)

        self.assertEqual(payload["text"], "hello")

    def test_empty_parts_returns_empty_string(self) -> None:
        message = Message()
        message.message_id = "msg-3"
        message.role = Role.ROLE_USER

        payload = extract_request_payload(message)

        self.assertEqual(payload["text"], "")


class BuildStatusMessageTest(unittest.TestCase):
    def test_builds_message_with_text_part(self) -> None:
        msg = build_status_message(context_id="ctx-1", task_id="task-1", text="working")
        self.assertEqual(msg.context_id, "ctx-1")
        self.assertEqual(msg.task_id, "task-1")
        self.assertEqual(msg.role, Role.ROLE_AGENT)
        self.assertEqual(msg.parts[0].text, "working")


class BuildStatusTest(unittest.TestCase):
    def test_builds_status_with_state_and_message(self) -> None:
        from a2a.types import TaskState
        status = build_status(
            context_id="ctx-1", task_id="task-1",
            state=TaskState.TASK_STATE_WORKING, text="working",
        )
        self.assertEqual(status.state, TaskState.TASK_STATE_WORKING)
        self.assertEqual(status.message.parts[0].text, "working")


class BuildArtifactTest(unittest.TestCase):
    def test_builds_artifact_with_data_part(self) -> None:
        from a2a.types import Artifact
        data = {"incident": {"name": "LASER_MOD_ERR", "priority": "high"}}
        artifact = build_artifact(artifact_data=data)
        self.assertIsInstance(artifact, Artifact)
        self.assertEqual(artifact.name, "faultManagement.Incident")
        self.assertTrue(artifact.artifact_id)


class EmitStatusUpdateTest(unittest.IsolatedAsyncioTestCase):
    async def test_enqueues_status_update_event(self) -> None:
        from a2a.types import TaskState
        request_context = _make_fake_request_context()
        event_queue = FakeEventQueue()
        await emit_status_update(
            request_context=request_context,
            event_queue=event_queue,
            context_id="ctx-1",
            task_id="task-1",
            state=TaskState.TASK_STATE_WORKING,
            text="working",
        )
        self.assertEqual(len(event_queue.events), 1)
        event = event_queue.events[0]
        self.assertTrue(hasattr(event, "status"))


def _make_fake_request_context() -> object:
    class FakeRequestContext:
        def __init__(self) -> None:
            self.current_task = None
    return FakeRequestContext()


if __name__ == "__main__":
    unittest.main()
