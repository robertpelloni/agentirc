import argparse
import asyncio
import socket
import ssl
import json
import re
from pathlib import Path

from simulator_core import (
    STATE_FILE,
    load_persistent_state,
    save_persistent_state,
    coerce_message_content,
    display_agent_name,
)
from services.agents import create_team, get_client

class HeadlessIRCBot:
    def __init__(self, server: str, port: int, channel: str, nick: str, use_tls: bool = False):
        self.server = server
        self.port = port
        self.channel = channel
        self.nick = nick
        self.use_tls = use_tls
        self.sock = None
        self.writer = None

        self.state = load_persistent_state(STATE_FILE)
        self.config = self.state["rooms"][self.state["active_room"]]["config"]
        self.agent_specs = self.state["agent_specs"]

        # Build the team
        self.team = create_team(self.config, self.agent_specs, self.state["global_config"])
        print(f"[{self.nick}] Initialized AutoGen team for room: {self.config['room_name']}")

    def connect(self):
        print(f"[{self.nick}] Connecting to {self.server}:{self.port} (TLS: {self.use_tls})...")
        raw_sock = socket.create_connection((self.server, self.port), timeout=10)
        if self.use_tls:
            context = ssl.create_default_context()
            self.sock = context.wrap_socket(raw_sock, server_hostname=self.server)
        else:
            self.sock = raw_sock

    async def send_raw(self, line: str):
        if self.writer:
            self.writer.write((line + "\r\n").encode("utf-8", errors="ignore"))
            await self.writer.drain()

    async def send_privmsg(self, target: str, text: str):
        # Basic chunking to avoid IRC line length limits
        normalized = " ".join(text.replace("\r", " ").replace("\n", " ").split())
        limit = 380
        remaining = normalized
        while remaining:
            chunk = remaining[:limit]
            await self.send_raw(f"PRIVMSG {target} :{chunk}")
            remaining = remaining[limit:]

    async def run(self):
        self.connect()
        # Use asyncio reader and writer for non-blocking I/O
        reader, self.writer = await asyncio.open_connection(sock=self.sock)

        await self.send_raw(f"NICK {self.nick}")
        await self.send_raw(f"USER {self.nick} 0 * :{self.nick} Headless Bot")

        joined = False

        while True:
            line_bytes = await reader.readline()
            if not line_bytes:
                print("Connection closed by server.")
                break

            line = line_bytes.decode("utf-8", errors="ignore").strip()

            if line.startswith("PING"):
                await self.send_raw(line.replace("PING", "PONG", 1))
                continue

            # Wait for 001 numeric (Welcome) to join the channel
            if not joined and (" 001 " in line or " 376 " in line or " 422 " in line):
                await self.send_raw(f"JOIN {self.channel}")
                print(f"[{self.nick}] Joined {self.channel}")
                joined = True

            # Basic PRIVMSG parsing
            match = re.match(r":([^!]+)!.* PRIVMSG ([^ ]+) :(.*)", line)
            if match:
                sender, target, content = match.groups()
                # Ignore messages from ourselves or other bots if needed
                if sender == self.nick:
                    continue

                # Check if the message is in our channel or a direct message
                reply_target = target if target != self.nick else sender

                print(f"[{sender} -> {reply_target}] {content}")
                await self.handle_message(sender, reply_target, content)

    async def handle_message(self, sender: str, reply_target: str, content: str):
        if content.startswith("!topic "):
            new_topic = content[7:].strip()
            self.config["topic"] = new_topic
            save_persistent_state(self.state, STATE_FILE)
            await self.send_privmsg(reply_target, f"Topic changed to: {new_topic}")
            # Rebuild team with new topic
            self.team = create_team(self.config, self.agent_specs, self.state["global_config"])
            return

        if content.startswith("!status"):
            agents = ", ".join(self.config["enabled_agents"])
            await self.send_privmsg(reply_target, f"Active agents: {agents} | Topic: {self.config['topic']}")
            return

        # If it's a normal message, feed it to the agent stream
        try:
            await self.send_privmsg(reply_target, f"* Swarm is formulating a response to {sender}... *")
            prompt = f"<{sender}> {content}"
            async for event in self.team.run_stream(task=prompt):
                source = getattr(event, "source", None)
                msg_content = coerce_message_content(getattr(event, "content", None))

                if not source or not msg_content or source.lower() == "user":
                    continue

                display_name = display_agent_name(source)
                await self.send_privmsg(reply_target, f"<{display_name}> {msg_content}")
        except Exception as exc:
            await self.send_privmsg(reply_target, f"Error generating response: {exc}")

async def main():
    parser = argparse.ArgumentParser(description="AgentIRC Headless IRC Bot")
    parser.add_argument("--server", type=str, default="irc.libera.chat")
    parser.add_argument("--port", type=int, default=6667, help="Port (use 6697 for TLS)")
    parser.add_argument("--channel", type=str, required=True)
    parser.add_argument("--nick", type=str, default="AgentIRCBot")
    parser.add_argument("--tls", action="store_true", help="Enable TLS connection")
    args = parser.parse_args()

    # Automatically set port if TLS is requested but port is still default
    port = args.port
    if args.tls and port == 6667:
        port = 6697

    bot = HeadlessIRCBot(
        server=args.server,
        port=port,
        channel=args.channel,
        nick=args.nick,
        use_tls=args.tls
    )

    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())
