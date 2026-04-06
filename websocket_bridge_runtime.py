from __future__ import annotations

import argparse
import asyncio
import json
import shutil
from datetime import datetime
from pathlib import Path

from simulator_core import OUTBOX_DIR, PROCESSED_DIR, list_payload_files, load_external_payload

RUNTIME_LOG = PROCESSED_DIR / "websocket_runtime_events.jsonl"


def log_websocket_event(event: dict) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    with RUNTIME_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")



def build_websocket_message(payload: dict) -> str:
    envelope = {
        "transport": "websocket",
        "sent_at": datetime.now().isoformat(),
        "payload": payload,
    }
    return json.dumps(envelope, ensure_ascii=False)


async def send_websocket_message(uri: str, message: str) -> dict:
    try:
        from websockets.asyncio.client import connect  # type: ignore
    except Exception:
        from websockets.client import connect  # type: ignore

    async with connect(uri) as websocket:
        await websocket.send(message)

    return {
        "transport": "websocket",
        "uri": uri,
        "message_length": len(message),
    }


async def process_outbox_payload(path: Path, uri: str, dry_run: bool) -> dict:
    payload = load_external_payload(path)
    message = build_websocket_message(payload)

    delivery = {
        "transport": "websocket",
        "uri": uri,
        "dry_run": dry_run,
        "message_length": len(message),
    }
    if not dry_run:
        delivery = await send_websocket_message(uri, message)

    processed_path = PROCESSED_DIR / path.name
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    shutil.move(str(path), str(processed_path))
    event = {
        "processed_at": datetime.now().isoformat(),
        "source_file": str(processed_path),
        "kind": payload.get("kind", "unknown"),
        "delivery": delivery,
    }
    log_websocket_event(event)
    return event


async def poll_outbox_once(uri: str, dry_run: bool) -> list[dict]:
    events: list[dict] = []
    for path in list_payload_files(OUTBOX_DIR, limit=1000):
        try:
            events.append(await process_outbox_payload(path, uri, dry_run))
        except Exception as exc:  # pragma: no cover
            error_event = {
                "processed_at": datetime.now().isoformat(),
                "source_file": str(path),
                "kind": "error",
                "error": str(exc),
            }
            log_websocket_event(error_event)
            events.append(error_event)
    return events



def runtime_status(uri: str) -> dict:
    return {
        "transport": "websocket",
        "uri": uri,
        "outbox_files": len(list_payload_files(OUTBOX_DIR, limit=1000)),
        "processed_files": len(list_payload_files(PROCESSED_DIR, limit=1000)),
        "runtime_log": str(RUNTIME_LOG),
    }


async def async_main() -> int:
    parser = argparse.ArgumentParser(description="AgentIRC websocket bridge runtime scaffold")
    parser.add_argument("--uri", type=str, required=True, help="WebSocket URI, e.g. ws://localhost:8765")
    parser.add_argument("--dry-run", action="store_true", help="Do not connect; only process and log payloads")
    parser.add_argument("--once", action="store_true", help="Process the outbox once and exit")
    parser.add_argument("--interval", type=float, default=2.0, help="Polling interval in seconds")
    args = parser.parse_args()

    if args.once:
        events = await poll_outbox_once(args.uri, args.dry_run)
        print(json.dumps({"status": runtime_status(args.uri), "events": events}, indent=2))
        return 0

    print(f"AgentIRC websocket bridge runtime polling started for {args.uri}.")
    while True:
        events = await poll_outbox_once(args.uri, args.dry_run)
        if events:
            print(json.dumps({"processed": len(events), "status": runtime_status(args.uri)}, indent=2))
        await asyncio.sleep(max(0.25, args.interval))


if __name__ == "__main__":
    raise SystemExit(asyncio.run(async_main()))
