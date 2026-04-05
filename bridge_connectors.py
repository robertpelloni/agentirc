from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from simulator_core import INBOX_DIR, sanitize_key


CONNECTOR_CATALOG: dict[str, str] = {
    "console": "Print payload delivery results to stdout for local debugging and runtime visibility.",
    "inbox": "Deliver payloads into the local `inbox/` directory for manual or app-driven import.",
    "jsonl": "Append delivery events to a JSONL file for downstream automation or auditing.",
}

JSONL_OUTPUT = Path("processed/connector_output.jsonl")



def build_connector_catalog_text() -> str:
    lines = ["**Bridge Connectors**"]
    for name, description in CONNECTOR_CATALOG.items():
        lines.append(f"- **{name}** — {description}")
    return "\n".join(lines)



def build_connector_payload_message(payload: dict[str, Any]) -> str:
    kind = payload.get("kind", "payload")
    if kind == "room_snapshot":
        return (
            f"room snapshot from {payload.get('room', 'unknown')} "
            f"topic={payload.get('topic', 'n/a')} entries={len(payload.get('entries', []))}"
        )
    if kind == "bridge_note":
        return (
            f"bridge note {payload.get('source_room', 'unknown')} -> {payload.get('target_room', 'unknown')}"
        )
    return json.dumps(payload, ensure_ascii=False)



def deliver_to_console(payload: dict[str, Any]) -> dict[str, Any]:
    message = build_connector_payload_message(payload)
    print(message)
    return {
        "connector": "console",
        "message": message,
    }



def deliver_to_inbox(payload: dict[str, Any], inbox_dir: Path = INBOX_DIR) -> dict[str, Any]:
    inbox_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    payload_kind = sanitize_key(str(payload.get("kind", "payload"))) or "payload"
    file_path = inbox_dir / f"agentirc-{payload_kind}-{timestamp}.json"
    file_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {
        "connector": "inbox",
        "destination": str(file_path),
    }



def deliver_to_jsonl(payload: dict[str, Any], output_path: Path = JSONL_OUTPUT) -> dict[str, Any]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return {
        "connector": "jsonl",
        "destination": str(output_path),
    }



def route_payload(payload: dict[str, Any], connector: str) -> dict[str, Any]:
    normalized = connector.strip().lower()
    if normalized == "console":
        return deliver_to_console(payload)
    if normalized == "inbox":
        return deliver_to_inbox(payload)
    if normalized == "jsonl":
        return deliver_to_jsonl(payload)
    raise ValueError(f"Unknown connector: {connector}")
