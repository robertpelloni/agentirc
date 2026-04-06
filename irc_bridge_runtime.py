from __future__ import annotations

import argparse
import json
import shutil
import socket
import ssl
import time
from datetime import datetime
from pathlib import Path

from simulator_core import OUTBOX_DIR, PROCESSED_DIR, list_payload_files, load_external_payload

IRC_LOG = PROCESSED_DIR / "irc_runtime_events.jsonl"
MAX_PRIVMSG_LEN = 380



def log_irc_event(event: dict) -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    with IRC_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")



def normalize_irc_text(text: str) -> str:
    return " ".join(text.replace("\r", " ").replace("\n", " ").split())



def chunk_irc_message(text: str, limit: int = MAX_PRIVMSG_LEN) -> list[str]:
    normalized = normalize_irc_text(text)
    if not normalized:
        return [""]

    chunks: list[str] = []
    remaining = normalized
    while len(remaining) > limit:
        split_at = remaining.rfind(" ", 0, limit)
        if split_at <= 0:
            split_at = limit
        chunks.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()
    if remaining:
        chunks.append(remaining)
    return chunks



def build_irc_message(payload: dict) -> str:
    kind = payload.get("kind", "payload")
    if kind == "room_snapshot":
        room = payload.get("room", "unknown")
        topic = payload.get("topic", "n/a")
        entries = payload.get("entries", [])
        preview = " | ".join(
            f"<{entry.get('author', 'unknown')}> {entry.get('content', '')}" for entry in entries[-3:]
        ) or "(no entries)"
        return f"[room_snapshot] room={room} topic={topic} preview={preview}"
    if kind == "bridge_note":
        source_room = payload.get("source_room", "unknown")
        target_room = payload.get("target_room", "unknown")
        content = payload.get("content", "")
        return f"[bridge_note] {source_room} -> {target_room}: {content}"
    return json.dumps(payload, ensure_ascii=False)



def payload_to_irc_lines(payload: dict, channel: str) -> list[str]:
    message = build_irc_message(payload)
    return [f"PRIVMSG {channel} :{chunk}\r\n" for chunk in chunk_irc_message(message)]



def open_irc_socket(server: str, port: int, use_tls: bool) -> socket.socket:
    sock = socket.create_connection((server, port), timeout=10)
    if use_tls:
        context = ssl.create_default_context()
        return context.wrap_socket(sock, server_hostname=server)
    return sock



def send_irc_line(sock: socket.socket, line: str) -> None:
    sock.sendall(line.encode("utf-8", errors="ignore"))



def process_outbox_payload(
    path: Path,
    server: str,
    port: int,
    channel: str,
    nick: str,
    user: str,
    use_tls: bool,
    dry_run: bool,
) -> dict:
    payload = load_external_payload(path)
    lines = payload_to_irc_lines(payload, channel)

    if not dry_run:
        sock = open_irc_socket(server, port, use_tls)
        try:
            send_irc_line(sock, f"NICK {nick}\r\n")
            send_irc_line(sock, f"USER {user} 0 * :{user}\r\n")
            send_irc_line(sock, f"JOIN {channel}\r\n")
            for line in lines:
                send_irc_line(sock, line)
        finally:
            try:
                sock.close()
            except Exception:
                pass

    processed_path = PROCESSED_DIR / path.name
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    shutil.move(str(path), str(processed_path))
    event = {
        "processed_at": datetime.now().isoformat(),
        "source_file": str(processed_path),
        "kind": payload.get("kind", "unknown"),
        "channel": channel,
        "dry_run": dry_run,
        "line_count": len(lines),
    }
    log_irc_event(event)
    return event



def poll_outbox_once(
    server: str,
    port: int,
    channel: str,
    nick: str,
    user: str,
    use_tls: bool,
    dry_run: bool,
) -> list[dict]:
    events: list[dict] = []
    for path in list_payload_files(OUTBOX_DIR, limit=1000):
        try:
            events.append(process_outbox_payload(path, server, port, channel, nick, user, use_tls, dry_run))
        except Exception as exc:  # pragma: no cover
            error_event = {
                "processed_at": datetime.now().isoformat(),
                "source_file": str(path),
                "kind": "error",
                "error": str(exc),
            }
            log_irc_event(error_event)
            events.append(error_event)
    return events



def main() -> int:
    parser = argparse.ArgumentParser(description="AgentIRC IRC bridge runtime scaffold")
    parser.add_argument("--server", type=str, default="irc.libera.chat")
    parser.add_argument("--port", type=int, default=6697)
    parser.add_argument("--channel", type=str, required=True)
    parser.add_argument("--nick", type=str, default="AgentIRCBot")
    parser.add_argument("--user", type=str, default="agentirc")
    parser.add_argument("--tls", action="store_true", help="Enable TLS for IRC connection")
    parser.add_argument("--dry-run", action="store_true", help="Do not connect; only process and log payloads")
    parser.add_argument("--once", action="store_true", help="Process the outbox once and exit")
    parser.add_argument("--interval", type=float, default=2.0, help="Polling interval in seconds")
    args = parser.parse_args()

    if args.once:
        events = poll_outbox_once(args.server, args.port, args.channel, args.nick, args.user, args.tls, args.dry_run)
        print(json.dumps({"events": events}, indent=2))
        return 0

    print("AgentIRC IRC bridge runtime polling started.")
    while True:
        events = poll_outbox_once(args.server, args.port, args.channel, args.nick, args.user, args.tls, args.dry_run)
        if events:
            print(json.dumps({"processed": len(events)}, indent=2))
        time.sleep(max(0.25, args.interval))


if __name__ == "__main__":
    raise SystemExit(main())
