from __future__ import annotations

import asyncio
from pathlib import Path

from client_example.client_main import run_main
from client_example.scenario_data import build_subscription_request


async def main() -> None:
    result = await run_main(
        env_path=Path(".env"),
        initial_input=build_subscription_request(),
        max_artifacts=5,
        log_sink=print,
        debug_enabled=False,
    )
    events = result if isinstance(result, list) else []
    artifact_count = sum(1 for e in events if e.get("kind") == "artifact")
    print(f"e2e result: events={len(events)} artifacts={artifact_count}")
    assert artifact_count == 5, f"Expected 5 artifacts, got {artifact_count}"
    print("e2e PASSED")


if __name__ == "__main__":
    asyncio.run(main())
