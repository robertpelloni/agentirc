import json
import tempfile
import unittest
from pathlib import Path

import bridge_runtime as runtime_module
from simulator_core import OUTBOX_DIR, PROCESSED_DIR, build_external_room_payload, make_default_store, make_entry, make_initial_rooms


AGENT_SPECS = {
    "Claude": {"model": "anthropic/claude-sonnet-4.6", "bio": "Nuanced and detailed."},
}


class BridgeRuntimeTests(unittest.TestCase):
    def test_process_outbox_payload_jsonl(self):
        persistent_state = make_default_store()
        rooms = make_initial_rooms(AGENT_SPECS, persistent_state)
        rooms["lobby"]["history"].append(make_entry("Claude", "hello runtime"))
        payload = build_external_room_payload("lobby", rooms["lobby"], 1)

        with tempfile.TemporaryDirectory() as temp_dir:
            outbox_dir = Path(temp_dir) / OUTBOX_DIR
            processed_dir = Path(temp_dir) / PROCESSED_DIR
            outbox_dir.mkdir(parents=True, exist_ok=True)
            payload_path = outbox_dir / "agentirc-room_snapshot-runtime.json"
            payload_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

            original_outbox = runtime_module.OUTBOX_DIR
            original_processed = runtime_module.PROCESSED_DIR
            original_log = runtime_module.RUNTIME_LOG
            try:
                runtime_module.OUTBOX_DIR = outbox_dir
                runtime_module.PROCESSED_DIR = processed_dir
                runtime_module.RUNTIME_LOG = processed_dir / "bridge_runtime_events.jsonl"
                event = runtime_module.process_outbox_payload(payload_path, "jsonl")
                self.assertEqual(event["kind"], "room_snapshot")
                self.assertEqual(event["connector"], "jsonl")
                self.assertTrue(processed_dir.joinpath(payload_path.name).exists())
                self.assertTrue(runtime_module.RUNTIME_LOG.exists())
            finally:
                runtime_module.OUTBOX_DIR = original_outbox
                runtime_module.PROCESSED_DIR = original_processed
                runtime_module.RUNTIME_LOG = original_log

    def test_poll_outbox_once_and_runtime_status(self):
        persistent_state = make_default_store()
        rooms = make_initial_rooms(AGENT_SPECS, persistent_state)
        rooms["lobby"]["history"].append(make_entry("Claude", "hello polling"))
        payload = build_external_room_payload("lobby", rooms["lobby"], 1)

        with tempfile.TemporaryDirectory() as temp_dir:
            outbox_dir = Path(temp_dir) / OUTBOX_DIR
            processed_dir = Path(temp_dir) / PROCESSED_DIR
            outbox_dir.mkdir(parents=True, exist_ok=True)
            payload_path = outbox_dir / "agentirc-room_snapshot-poll.json"
            payload_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

            original_outbox = runtime_module.OUTBOX_DIR
            original_processed = runtime_module.PROCESSED_DIR
            original_log = runtime_module.RUNTIME_LOG
            try:
                runtime_module.OUTBOX_DIR = outbox_dir
                runtime_module.PROCESSED_DIR = processed_dir
                runtime_module.RUNTIME_LOG = processed_dir / "bridge_runtime_events.jsonl"
                events = runtime_module.poll_outbox_once("console")
                self.assertEqual(len(events), 1)
                status = runtime_module.runtime_status("console")
                self.assertEqual(status["connector"], "console")
                self.assertEqual(status["outbox_files"], 0)
                self.assertEqual(status["processed_files"], 1)
            finally:
                runtime_module.OUTBOX_DIR = original_outbox
                runtime_module.PROCESSED_DIR = original_processed
                runtime_module.RUNTIME_LOG = original_log


if __name__ == "__main__":
    unittest.main()
