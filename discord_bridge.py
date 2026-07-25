import asyncio
import os
import sys
import logging
import json
from datetime import datetime
from pathlib import Path

# Ensure the parent directory is in the sys.path so we can import simulator_core
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from simulator_core import INBOX_DIR, OUTBOX_DIR, list_payload_files, load_external_payload

# Setup standard logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("discord_bridge")

# Try to import discord
try:
    import discord
except ImportError:
    logger.error("discord.py is not installed. Please run `pip install discord.py`")
    sys.exit(1)

class DiscordBridge(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.polling_task = None
        self.target_channel_id = int(os.environ.get("DISCORD_CHANNEL_ID", "0"))

    async def on_ready(self):
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info("------")
        if self.target_channel_id != 0:
            self.polling_task = self.loop.create_task(self.poll_outbox())

    async def on_message(self, message):
        # Don't respond to ourselves
        if message.author == self.user:
            return

        # Only process messages in the target channel if specified
        if self.target_channel_id != 0 and message.channel.id != self.target_channel_id:
            return

        # Write incoming discord message to INBOX for the swarm to read
        payload = {
            "kind": "chat",
            "source": "discord",
            "author": str(message.author.display_name),
            "content": message.content,
            "timestamp": datetime.now().isoformat()
        }

        INBOX_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        file_path = INBOX_DIR / f"agentirc-discord-{timestamp}.json"
        file_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

        logger.info(f"Delivered message from {message.author} to INBOX")

    async def poll_outbox(self):
        logger.info(f"Started polling OUTBOX for channel {self.target_channel_id}")
        channel = self.get_channel(self.target_channel_id)
        if not channel:
            logger.error(f"Could not find channel with ID {self.target_channel_id}")
            return

        while not self.is_closed():
            try:
                for path in list_payload_files(OUTBOX_DIR, limit=10):
                    payload = load_external_payload(path)

                    # Convert payload to discord message
                    kind = payload.get("kind", "unknown")
                    text_content = ""
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
                        text_content = json.dumps(payload, ensure_ascii=False)

                    # Send to discord (truncate if needed)
                    safe_content = text_content[:1990] + ("..." if len(text_content) > 1990 else "")
                    await channel.send(safe_content)

                    # Clean up file
                    path.unlink()
                    logger.info(f"Processed and deleted OUTBOX payload {path.name}")

            except Exception as e:
                logger.error(f"Error polling outbox: {e}")

            await asyncio.sleep(2.0)

if __name__ == "__main__":
    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        logger.error("Please set the DISCORD_TOKEN environment variable.")
        sys.exit(1)

    intents = discord.Intents.default()
    intents.message_content = True
    client = DiscordBridge(intents=intents)
    client.run(token)
