from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable, Mapping

from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.types import AgentCard, Task, TaskArtifactUpdateEvent, TaskState

from common.a2a_adapter import build_artifact, build_status, emit_status_update
from common.logging_utils import format_stage_log, summarize_text
from server_example.constants_data import (
    ARTIFACT_SEND_INTERVAL_SECONDS,
    COMPLETED_MESSAGE,
    INCIDENT_ARTIFACT_DATA,
    SUBMITTED_MESSAGE,
    WORKING_MESSAGE,
)

SleepFn = Callable[[float], Awaitable[None]]


async def execute_server_flow(
    *,
    request_context: RequestContext,
    event_queue: EventQueue,
    agent_card: AgentCard,
    prompt_server: object,
    max_artifacts: int | None = None,
    sleep_fn: SleepFn | None = None,
    artifact_send_interval_seconds: float = ARTIFACT_SEND_INTERVAL_SECONDS,
    incident_artifact_data: Mapping[str, object] | None = None,
    log_sink: object | None = None,
    debug_enabled: bool = False,
) -> None:
    resolved_sleep = sleep_fn or asyncio.sleep
    resolved_artifact_data = INCIDENT_ARTIFACT_DATA if incident_artifact_data is None else incident_artifact_data
    resolved_task_id = request_context.task_id or ""
    resolved_context_id = request_context.context_id or ""

    payload_text = request_context.message.parts[0].text if request_context.message.parts else ""
    if log_sink is not None:
        log_sink(
            format_stage_log(
                role="server",
                stage="request-inbound",
                detail=f"text={summarize_text(payload_text)}",
            )
        )

    check_result = prompt_server.check_task_prompt(processed_prompt_text=payload_text)
    if not check_result.success:
        if log_sink is not None:
            log_sink(
                format_stage_log(
                    role="server",
                    stage="prompt-check-failed",
                    detail=f"failure={check_result.failure}",
                )
            )
        raise RuntimeError(f"Prompt compliance failed: {check_result.failure}")

    if log_sink is not None:
        log_sink(
            format_stage_log(
                role="server",
                stage="prompt-check-passed",
                detail="starting streaming artifact push",
            )
        )

    task = Task(
        id=resolved_task_id,
        context_id=resolved_context_id,
        status=build_status(
            context_id=resolved_context_id,
            task_id=resolved_task_id,
            state=TaskState.TASK_STATE_SUBMITTED,
            text=SUBMITTED_MESSAGE,
        ),
    )
    request_context.current_task = Task()
    request_context.current_task.CopyFrom(task)
    await event_queue.enqueue_event(task)

    await emit_status_update(
        request_context=request_context,
        event_queue=event_queue,
        context_id=resolved_context_id,
        task_id=resolved_task_id,
        state=TaskState.TASK_STATE_WORKING,
        text=WORKING_MESSAGE,
    )

    artifacts_pushed = 0
    try:
        while max_artifacts is None or artifacts_pushed < max_artifacts:
            await event_queue.enqueue_event(
                TaskArtifactUpdateEvent(
                    task_id=resolved_task_id,
                    context_id=resolved_context_id,
                    artifact=build_artifact(artifact_data=resolved_artifact_data),
                    last_chunk=True,
                )
            )
            artifacts_pushed += 1
            if log_sink is not None:
                log_sink(
                    format_stage_log(
                        role="server",
                        stage="artifact-pushed",
                        detail=f"count={artifacts_pushed}",
                    )
                )
                log_sink(
                    json.dumps(
                        dict(resolved_artifact_data),
                        ensure_ascii=False,
                        indent=2,
                    )
                )
            await resolved_sleep(artifact_send_interval_seconds)
    finally:
        await emit_status_update(
            request_context=request_context,
            event_queue=event_queue,
            context_id=resolved_context_id,
            task_id=resolved_task_id,
            state=TaskState.TASK_STATE_COMPLETED,
            text=COMPLETED_MESSAGE,
        )
        if log_sink is not None:
            log_sink(
                format_stage_log(
                    role="server",
                    stage="task-completed",
                    detail=f"artifacts_pushed={artifacts_pushed}",
                )
            )
