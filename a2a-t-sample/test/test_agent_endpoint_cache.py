from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "a2a-t-sample" / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from common.agent_endpoint_cache import resolve_preferred_interface


class ResolvePreferredInterfaceTest(unittest.TestCase):
    def test_extracts_url_from_supported_interfaces(self) -> None:
        agent_card = {
            "name": "Test Agent",
            "supportedInterfaces": [
                {
                    "protocolBinding": "HTTP+JSON",
                    "protocolVersion": "1.0.0",
                    "url": "http://127.0.0.1:8000",
                }
            ],
        }
        endpoint = resolve_preferred_interface(agent_card)
        self.assertEqual(endpoint.url, "http://127.0.0.1:8000")
        self.assertEqual(endpoint.protocol_binding, "HTTP+JSON")
        self.assertEqual(endpoint.protocol_version, "1.0.0")
        self.assertEqual(endpoint.agent_name, "Test Agent")

    def test_missing_supported_interfaces_raises(self) -> None:
        with self.assertRaises(ValueError):
            resolve_preferred_interface({"name": "x"})

    def test_invalid_url_raises(self) -> None:
        agent_card = {
            "name": "x",
            "supportedInterfaces": [{"protocolBinding": "HTTP+JSON", "url": "not-a-url"}],
        }
        with self.assertRaises(ValueError):
            resolve_preferred_interface(agent_card)

    def test_empty_interfaces_raises(self) -> None:
        agent_card = {"name": "x", "supportedInterfaces": []}
        with self.assertRaises(ValueError):
            resolve_preferred_interface(agent_card)


if __name__ == "__main__":
    unittest.main()
