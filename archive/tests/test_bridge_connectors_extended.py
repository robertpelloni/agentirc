import json
import tempfile
import unittest
from pathlib import Path

from bridge_connectors import (
    route_payload,
    deliver_to_console,
)

PAYLOAD = {
    "kind": "bridge_note",
    "source": "room_a",
    "target": "room_b",
    "content": "Secret note.",
}

class BridgeConnectorExtendedTests(unittest.TestCase):
    def test_deliver_to_console(self):
        # Console connector prints to stdout and returns the formatted message
        result = deliver_to_console(PAYLOAD)
        self.assertEqual(result["connector"], "console")
        self.assertIn("message", result)

    def test_route_payload_unknown_connector(self):
        # Should raise ValueError or default gracefully
        with self.assertRaises(ValueError) as context:
            route_payload(PAYLOAD, "nonexistent_connector")
        self.assertIn("Unknown connector", str(context.exception))

    def test_route_payload_console(self):
        result = route_payload(PAYLOAD, "console")
        self.assertEqual(result["connector"], "console")

if __name__ == "__main__":
    unittest.main()
