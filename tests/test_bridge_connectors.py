import json
import tempfile
import unittest
from pathlib import Path

from bridge_connectors import (
    JSONL_OUTPUT,
    build_connector_catalog_text,
    build_connector_payload_message,
    deliver_to_inbox,
    deliver_to_jsonl,
    route_payload,
)


PAYLOAD = {
    "kind": "room_snapshot",
    "room": "lobby",
    "topic": "Test Topic",
    "entries": [{"author": "Claude", "content": "hello"}],
}


class BridgeConnectorTests(unittest.TestCase):
    def test_catalog_text_lists_connectors(self):
        text = build_connector_catalog_text()
        self.assertIn("console", text)
        self.assertIn("inbox", text)
        self.assertIn("jsonl", text)

    def test_payload_message(self):
        message = build_connector_payload_message(PAYLOAD)
        self.assertIn("room snapshot", message)
        self.assertIn("lobby", message)

    def test_deliver_to_inbox(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = deliver_to_inbox(PAYLOAD, Path(temp_dir))
            output = Path(result["destination"])
            self.assertTrue(output.exists())
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["room"], "lobby")

    def test_deliver_to_jsonl(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / JSONL_OUTPUT.name
            result = deliver_to_jsonl(PAYLOAD, output)
            self.assertEqual(Path(result["destination"]), output)
            self.assertTrue(output.exists())
            line = output.read_text(encoding="utf-8").strip()
            payload = json.loads(line)
            self.assertEqual(payload["kind"], "room_snapshot")

    def test_route_payload(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = route_payload(PAYLOAD, "inbox")
            self.assertEqual(result["connector"], "inbox")


if __name__ == "__main__":
    unittest.main()
