import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from bridge_connectors import deliver_to_discord

PAYLOAD = {
    "kind": "room_snapshot",
    "room": "lobby",
    "topic": "Test",
    "entries": [{"author": "Claude", "content": "hello"}]
}

class BridgeDiscordTests(unittest.TestCase):
    def test_deliver_to_discord_requires_endpoint(self):
        with self.assertRaises(ValueError):
            deliver_to_discord(PAYLOAD, None)

    def test_deliver_to_discord_local_server(self):
        received: list[bytes] = []

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get("Content-Length", "0"))
                received.append(self.rfile.read(length))
                self.send_response(200)
                self.end_headers()

            def log_message(self, format, *args):
                return

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.handle_request, daemon=True)
        thread.start()
        try:
            endpoint = f"http://127.0.0.1:{server.server_port}/hook"
            result = deliver_to_discord(PAYLOAD, endpoint)
            thread.join(timeout=2)
            self.assertEqual(result["connector"], "discord")
            self.assertEqual(result["status"], 200)
            self.assertTrue(received)
            body = json.loads(received[0].decode("utf-8"))
            # Discord expects exactly a "content" key at the root.
            self.assertIn("content", body)
            self.assertIn("Room Snapshot: lobby", body["content"])
            self.assertIn("Claude**: hello", body["content"])
        finally:
            server.server_close()

if __name__ == "__main__":
    unittest.main()
