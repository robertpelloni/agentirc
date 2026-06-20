import argparse
import asyncio
import os
import discord
from dotenv import load_dotenv

from simulator_core import (
    STATE_FILE,
    load_persistent_state,
    save_persistent_state,
    coerce_message_content,
    display_agent_name,
)
from services.agents import create_team

class AgentIRCDiscordBot(discord.Client):
    def __init__(self, target_channel_id: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_channel_id = target_channel_id

        self.state = load_persistent_state(STATE_FILE)
        self.config = self.state["rooms"][self.state["active_room"]]["config"]
        self.agent_specs = self.state["agent_specs"]

        # Build the team
        self.team = create_team(self.config, self.agent_specs, self.state["global_config"])
        print(f"[Discord] Initialized AutoGen team for room: {self.config['room_name']}")

    async def on_ready(self):
        print(f"[Discord] Logged in as {self.user} (ID: {self.user.id})")
        channel = self.get_channel(self.target_channel_id)
        if channel:
            await channel.send(f"**[AgentIRC Swarm Online]** Connected to room: `{self.config['room_name']}` | Topic: `{self.config['topic']}`")
        else:
            print(f"[Discord] WARNING: Cannot find target channel ID {self.target_channel_id}")

    async def on_message(self, message: discord.Message):
        # Ignore messages from ourselves or outside the target channel
        if message.author == self.user or message.channel.id != self.target_channel_id:
            return

        content = message.content.strip()
        sender = message.author.display_name

        if content.startswith("!topic "):
            new_topic = content[7:].strip()
            self.config["topic"] = new_topic
            save_persistent_state(self.state, STATE_FILE)
            await message.channel.send(f"**[System]** Topic changed to: `{new_topic}`")
            # Rebuild team with new topic
            self.team = create_team(self.config, self.agent_specs, self.state["global_config"])
            return

        if content.startswith("!status"):
            agents = ", ".join(self.config["enabled_agents"])
            await message.channel.send(f"**[System]** Active agents: `{agents}`\n**[System]** Topic: `{self.config['topic']}`")
            return

        # Regular message handling
        try:
            # Send typing indicator
            async with message.channel.typing():
                prompt = f"<{sender}> {content}"
                async for event in self.team.run_stream(task=prompt):
                    source = getattr(event, "source", None)
                    msg_content = coerce_message_content(getattr(event, "content", None))

                    if not source or not msg_content or source.lower() == "user":
                        continue

                    display_name = display_agent_name(source)
                    # Stream the response chunk back to discord
                    # Discord limits messages to 2000 chars
                    limit = 1990
                    remaining = msg_content
                    while remaining:
                        chunk = remaining[:limit]
                        await message.channel.send(f"**<{display_name}>** {chunk}")
                        remaining = remaining[limit:]
        except Exception as exc:
            await message.channel.send(f"**[System Error]** Generating response failed: {exc}")


def main():
    parser = argparse.ArgumentParser(description="AgentIRC Bidirectional Discord Bridge Bot")
    parser.add_argument("--channel", type=int, required=True, help="Discord Channel ID to bind the swarm to")
    args = parser.parse_args()

    load_dotenv(override=True)
    token = os.environ.get("DISCORD_BOT_TOKEN")
    if not token:
        print("[ERROR] DISCORD_BOT_TOKEN environment variable not found.")
        print("Please set it in your .env file or export it directly.")
        return 1

    intents = discord.Intents.default()
    intents.message_content = True

    bot = AgentIRCDiscordBot(target_channel_id=args.channel, intents=intents)
    bot.run(token)

if __name__ == "__main__":
    raise SystemExit(main())
