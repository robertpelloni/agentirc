import asyncio
import logging
from typing import Optional

# Setup standard logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("headless_irc")

class HeadlessIRCClient:
    """A minimal headless IRC client to interface with the simulator."""
    def __init__(self, host: str, port: int, channel: str, nick: str):
        self.host = host
        self.port = port
        self.channel = channel
        self.nick = nick
        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None

    async def connect(self):
        logger.info(f"Connecting to {self.host}:{self.port}...")
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        await self.send(f"USER {self.nick} 0 * :{self.nick}")
        await self.send(f"NICK {self.nick}")

    async def send(self, message: str):
        if self.writer:
            logger.debug(f"> {message}")
            self.writer.write((message + "\r\n").encode())
            await self.writer.drain()

    async def run(self):
        await self.connect()
        while True:
            if not self.reader:
                break
            line = await self.reader.readline()
            if not line:
                break
            line_str = line.decode('utf-8', errors='ignore').strip()
            logger.debug(f"< {line_str}")

            # Respond to PING
            if line_str.startswith("PING"):
                await self.send(line_str.replace("PING", "PONG", 1))

            # Auto-join on 001 (welcome) or similar numeric
            if " 001 " in line_str or " 376 " in line_str:
                await self.send(f"JOIN {self.channel}")

            # Intercept PRIVMSG for the swarm
            if "PRIVMSG" in line_str:
                self.handle_privmsg(line_str)

    def handle_privmsg(self, raw_line: str):
        try:
            parts = raw_line.split(" ", 3)
            if len(parts) < 4:
                return
            sender = parts[0][1:].split("!")[0]
            target = parts[2]
            message = parts[3][1:]

            # Simple bypass if the message is from ourselves
            if sender == self.nick:
                return

            logger.info(f"[{target}] <{sender}> {message}")

            # Here we would normally pipe this message into simulator_core.py and the AutoGen swarm
            # For now, it's a stub to acknowledge receipt.

        except Exception as e:
            logger.error(f"Error parsing PRIVMSG: {e}")

if __name__ == "__main__":
    client = HeadlessIRCClient("irc.libera.chat", 6667, "#agentirc-headless", "AgentSwarmBot")
    try:
        asyncio.run(client.run())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
