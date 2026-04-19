import unittest
from websocket_bridge_runtime import build_websocket_message

class WebsocketBridgeRuntimeExtendedTests(unittest.TestCase):
    def test_build_websocket_message_missing_kind(self):
        # Even with missing kind, it should format something, usually fallback to generic
        payload = {"source": "alpha", "target": "beta"}
        msg = build_websocket_message(payload)
        self.assertIn("alpha", msg)

if __name__ == "__main__":
    unittest.main()
