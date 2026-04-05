from __future__ import annotations

import argparse
import json
import shutil
import time
from datetime import datetime
from pathlib import Path

from simulator_core import INBOX_DIR, OUTBOX_DIR, PROCESSED_DIR, list_payload_files, load_external_payload

RUNTIME_LOG = PROCESSED_DIR / "bridge_runtime_events.jsonl"


def log_runtime_event(event: dict) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    with RUNTIME_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")



def process_outbox_payload(path: Path) -> dict:
    payload = load_external_payload(path)
    processed_path = PROCESSED_DIR / path.name
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    shutil.move(str(path), str(processed_path))
    event = {
        "processed_at": datetime.now().isoformat(),
        "source_file": str(processed_path),
        "kind": payload.get("kind", "unknown"),
        "room": payload.get("room") or payload.get("target_room"),
    }
    log_runtime_event(event)
    return event



def poll_outbox_once() -> list[dict]:
    events: list[dict] = []
    for path in list_payload_files(OUTBOX_DIR, limit=1000):
        try:
            events.append(process_outbox_payload(path))
        except Exception as exc:  # pragma: no cover - defensive runtime logging
            error_event = {
                "processed_at": datetime.now().isoformat(),
                "source_file": str(path),
                "kind": "error",
                "error": str(exc),
            }
            log_runtime_event(error_event)
            events.append(error_event)
    return events



def runtime_status() -> dict:
    return {
        "outbox_files": len(list_payload_files(OUTBOX_DIR, limit=1000)),
        "inbox_files": len(list_payload_files(INBOX_DIR, limit=1000)),
        "processed_files": len(list_payload_files(PROCESSED_DIR, limit=1000)),
        "runtime_log": str(RUNTIME_LOG),
    }



def main() -> int:
    parser = argparse.ArgumentParser(description="AgentIRC external bridge runtime scaffold")
    parser.add_argument("--once", action="store_true", help="Process the outbox once and exit")
    parser.add_argument("--interval", type=float, default=2.0, help="Polling interval in seconds")
    args = parser.parse_args()

    if args.once:
        events = poll_outbox_once()
        print(json.dumps({"status": runtime_status(), "events": events}, indent=2))
        return 0

    print("AgentIRC bridge runtime polling started.")
    while True:
        events = poll_outbox_once()
        if events:
            print(json.dumps({"processed": len(events), "status": runtime_status()}, indent=2))
        time.sleep(max(0.25, args.interval))


if __name__ == "__main__":
    raise SystemExit(main())
