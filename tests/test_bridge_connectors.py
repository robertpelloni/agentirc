import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from bridge_connectors import (
    JSONL_OUTPUT,
    build_connector_catalog_text,
    build_connector_payload_message,
    deliver_to_inbox,
    deliver_to_jsonl,
    deliver_to_webhook,
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

    def test_deliver_to_webhook_requires_endpoint(self):
        with self.assertRaises(ValueError):
            deliver_to_webhook(PAYLOAD, None)

    def test_deliver_to_webhook_local_server(self):
        received: list[bytes] = []

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):  # type: ignore[override]
                length = int(self.headers.get("Content-Length", "0"))
                received.append(self.rfile.read(length))
                self.send_response(200)
                self.end_headers()

            def log_message(self, format, *args):  # noqa: A003
                return

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.handle_request, daemon=True)
        thread.start()
        try:
            endpoint = f"http://127.0.0.1:{server.server_port}/hook"
            result = deliver_to_webhook(PAYLOAD, endpoint)
            thread.join(timeout=2)
            self.assertEqual(result["connector"], "webhook")
            self.assertEqual(result["status"], 200)
            self.assertTrue(received)
            body = json.loads(received[0].decode("utf-8"))
            self.assertEqual(body["kind"], "room_snapshot")
        finally:
            server.server_close()

    def test_route_payload(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = route_payload(PAYLOAD, "inbox")
            self.assertEqual(result["connector"], "inbox")


if __name__ == "__main__":
    unittest.main()
