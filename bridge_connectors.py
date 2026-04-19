from __future__ import annotations

import json
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from typing import Any

from simulator_core import INBOX_DIR, sanitize_key


CONNECTOR_CATALOG: dict[str, str] = {
    "console": "Print payload delivery results to stdout for local debugging and runtime visibility.",
    "inbox": "Deliver payloads into the local `inbox/` directory for manual or app-driven import.",
    "jsonl": "Append delivery events to a JSONL file for downstream automation or auditing.",
    "webhook": "Deliver payloads via HTTP POST to a remote endpoint. Requires --endpoint flag.",
    "discord": "Deliver payloads formatted as Discord chat messages. Requires --endpoint flag with Discord Webhook URL.",
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



def deliver_to_webhook(payload: dict[str, Any], endpoint: str | None) -> dict[str, Any]:
    if not endpoint:
        raise ValueError("Webhook connector requires an endpoint.")

    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            status = response.status
    except Exception as exc:
        status = str(exc)

    return {
        "connector": "webhook",
        "destination": endpoint,
        "status": status,
    }



def deliver_to_discord(payload: dict[str, Any], endpoint: str | None) -> dict[str, Any]:
    if not endpoint:
        raise ValueError("Discord connector requires a webhook endpoint URL.")

    # Map the internal AgentIRC payload into a Discord-friendly text message
    kind = payload.get("kind", "unknown")
    if kind == "room_snapshot":
        text_content = f"**Room Snapshot: {payload.get('room', 'n/a')}**\n"
        text_content += f"*Topic: {payload.get('topic', 'n/a')}*\n\n"
        for entry in payload.get("entries", []):
            author = entry.get("author", "unknown")
            content = entry.get("content", "")
            text_content += f"**{author}**: {content}\n"
    elif kind == "bridge_note":
        source = payload.get("source", "n/a")
        target = payload.get("target", "n/a")
        content = payload.get("content", "")
        text_content = f"**Bridge Note from {source} to {target}**\n\n{content}"
    else:
        text_content = build_connector_payload_message(payload)

    # Discord 'content' restricts to 2000 chars. Truncate gracefully.
    discord_payload = {
        "content": text_content[:1990] + ("..." if len(text_content) > 1990 else "")
    }

    req = urllib.request.Request(
        endpoint,
        data=json.dumps(discord_payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            status = response.status
    except Exception as exc:
        status = str(exc)

    return {
        "connector": "discord",
        "destination": endpoint,
        "status": status,
    }



def route_payload(payload: dict[str, Any], connector: str, endpoint: str | None = None) -> dict[str, Any]:
    normalized = connector.strip().lower()
    if normalized == "console":
        return deliver_to_console(payload)
    if normalized == "inbox":
        return deliver_to_inbox(payload)
    if normalized == "jsonl":
        return deliver_to_jsonl(payload)
    if normalized == "webhook":
        return deliver_to_webhook(payload, endpoint)
    if normalized == "discord":
        return deliver_to_discord(payload, endpoint)
    raise ValueError(f"Unknown connector: {connector}")
