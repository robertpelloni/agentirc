import json
import tempfile
import unittest
from pathlib import Path

from simulator_core import OUTBOX_DIR, make_entry, make_initial_rooms, make_default_store, build_external_room_payload
from websocket_bridge_runtime import build_websocket_message, runtime_status, process_outbox_payload


AGENT_SPECS = {
    "Claude": {"model": "anthropic/claude-sonnet-4.6", "bio": "Nuanced and detailed."},
}


class WebsocketBridgeRuntimeTests(unittest.IsolatedAsyncioTestCase):
    def test_build_websocket_message(self):
        payload = {"kind": "bridge_note", "content": "hello"}
        message = build_websocket_message(payload)
        envelope = json.loads(message)
        self.assertEqual(envelope["transport"], "websocket")
        self.assertEqual(envelope["payload"]["kind"], "bridge_note")

    async def test_process_outbox_payload_dry_run(self):
        persistent_state = make_default_store()
        rooms = make_initial_rooms(AGENT_SPECS, persistent_state)
        rooms["lobby"]["history"].append(make_entry("Claude", "hello world"))
        payload = build_external_room_payload("lobby", rooms["lobby"], 1)

        with tempfile.TemporaryDirectory() as temp_dir:
            outbox_dir = Path(temp_dir) / OUTBOX_DIR
            outbox_dir.mkdir(parents=True, exist_ok=True)
            path = outbox_dir / "agentirc-room_snapshot-test.json"
            path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

            import websocket_bridge_runtime as runtime_module
            original_outbox = runtime_module.OUTBOX_DIR
            original_processed = runtime_module.PROCESSED_DIR
            try:
                runtime_module.OUTBOX_DIR = outbox_dir
                runtime_module.PROCESSED_DIR = Path(temp_dir) / "processed"
                event = await process_outbox_payload(path, "ws://localhost:8765", True)
                self.assertEqual(event["kind"], "room_snapshot")
                self.assertTrue(runtime_module.PROCESSED_DIR.joinpath(path.name).exists())
                status = runtime_status("ws://localhost:8765")
                self.assertEqual(status["transport"], "websocket")
            finally:
                runtime_module.OUTBOX_DIR = original_outbox
                runtime_module.PROCESSED_DIR = original_processed


if __name__ == "__main__":
    unittest.main()
