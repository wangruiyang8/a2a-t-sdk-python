from __future__ import annotations

import sys
import unittest
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "a2a-t-sample" / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from common.registry_client import (
    query_by_name_org,
    register_agentcard,
    resolve_registry_center_url,
)


class _FakeResponse:
    def __init__(self, *, status_code: int, json_data: Any = None, text: str = "") -> None:
        self.status_code = status_code
        self._json_data = json_data
        self.text = text

    def json(self) -> Any:
        if self._json_data is None:
            raise ValueError("no json")
        return self._json_data


class _FakeHttpClient:
    def __init__(self, *, responses: list[_FakeResponse] | None = None, exc: Exception | None = None) -> None:
        self._responses = list(responses or [])
        self._exc = exc
        self.post_calls: list[dict[str, Any]] = []
        self.get_calls: list[dict[str, Any]] = []
        self.closed = False

    async def post(self, url: str, json: dict[str, Any]) -> _FakeResponse:
        self.post_calls.append({"url": url, "json": json})
        if self._exc is not None:
            raise self._exc
        return self._responses.pop(0)

    async def get(self, url: str) -> _FakeResponse:
        self.get_calls.append({"url": url})
        if self._exc is not None:
            raise self._exc
        return self._responses.pop(0)

    async def aclose(self) -> None:
        self.closed = True


class ResolveRegistryCenterUrlTest(unittest.TestCase):
    def test_defaults_to_localhost_5001(self) -> None:
        url = resolve_registry_center_url(env_path=Path("/nonexistent/.env"))
        self.assertEqual(url, "http://127.0.0.1:5001")

    def test_reads_from_env_file(self) -> None:
        import os
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False, encoding="utf-8") as f:
            f.write("REGISTRY_CENTER_HOST=10.0.0.1\nREGISTRY_CENTER_PORT=6001\n")
            tmp_path = Path(f.name)
        try:
            url = resolve_registry_center_url(env_path=tmp_path)
            self.assertEqual(url, "http://10.0.0.1:6001")
        finally:
            os.unlink(str(tmp_path))


class RegisterAgentcardTest(unittest.IsolatedAsyncioTestCase):
    async def test_success_returns_success_status(self) -> None:
        client = _FakeHttpClient(responses=[_FakeResponse(status_code=201, json_data={})])
        result = await register_agentcard(
            registration_payload={"agentCards": [{"name": "Test"}]},
            registry_center_url="http://127.0.0.1:5001",
            http_client=client,
        )
        self.assertEqual(result["status"], "success")
        self.assertEqual(len(client.post_calls), 1)
        self.assertIn("/rest/v1/registry-center/agent-cards", client.post_calls[0]["url"])

    async def test_non_201_returns_failed(self) -> None:
        client = _FakeHttpClient(responses=[_FakeResponse(status_code=500, json_data={"error": "x"})])
        result = await register_agentcard(
            registration_payload={"agentCards": []},
            registry_center_url="http://127.0.0.1:5001",
            http_client=client,
        )
        self.assertEqual(result["status"], "failed")

    async def test_exception_returns_failed(self) -> None:
        client = _FakeHttpClient(exc=ConnectionError("refused"))
        result = await register_agentcard(
            registration_payload={"agentCards": []},
            registry_center_url="http://127.0.0.1:5001",
            http_client=client,
        )
        self.assertEqual(result["status"], "failed")
        self.assertIn("refused", result["message"])


class QueryByNameOrgTest(unittest.IsolatedAsyncioTestCase):
    async def test_success_returns_agent_cards(self) -> None:
        card = {"name": "Test Agent", "provider": {"organization": "SampleOrg"}}
        client = _FakeHttpClient(responses=[_FakeResponse(status_code=200, json_data={"agentCards": [card]})])
        result = await query_by_name_org(
            organization="SampleOrg",
            name="Test Agent",
            registry_center_url="http://127.0.0.1:5001",
            http_client=client,
        )
        self.assertEqual(result["agentCards"], [card])
        self.assertEqual(len(client.get_calls), 1)
        self.assertIn("/rest/v1/registry-center/agent-cards/SampleOrg/Test%20Agent", client.get_calls[0]["url"])

    async def test_404_returns_empty_agent_cards(self) -> None:
        client = _FakeHttpClient(responses=[_FakeResponse(status_code=404, json_data={"errors": {}})])
        result = await query_by_name_org(
            organization="SampleOrg",
            name="Missing",
            registry_center_url="http://127.0.0.1:5001",
            http_client=client,
        )
        self.assertEqual(result["agentCards"], [])

    async def test_exception_returns_empty(self) -> None:
        client = _FakeHttpClient(exc=ConnectionError("refused"))
        result = await query_by_name_org(
            organization="SampleOrg",
            name="Test",
            registry_center_url="http://127.0.0.1:5001",
            http_client=client,
        )
        self.assertEqual(result["agentCards"], [])


if __name__ == "__main__":
    unittest.main()
