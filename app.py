import os
import asyncio
import chainlit as cl
from datetime import datetime
from dotenv import load_dotenv

# --- Python 3.14 Compatibility Patch ---
import anyio.to_thread
import typing

async def patched_run_sync(func: typing.Callable, *args, **kwargs):
    kwargs.pop("limiter", None)
    kwargs.pop("abandon_on_cancel", None)
    return await asyncio.to_thread(func, *args, **kwargs)

anyio.to_thread.run_sync = patched_run_sync
# ---------------------------------------

# AutoGen 0.4+ modular imports
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat, SelectorGroupChat
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.messages import AgentEvent, ChatMessage

load_dotenv(override=True)

# --- Configuration & Specs ---
LOG_FILE = "irc_session.log"

AGENT_SPECS = {
    "Claude": {
        "model": "anthropic/claude-sonnet-4.6",
        "color": "#ffaa00",
        "bio": "Nuanced and detailed."
    },
    "GPT_5": {
        "model": "openai/gpt-5.3-chat",
        "color": "#00ff00",
        "bio": "Logical and concise."
    },
    "Gemini": {
        "model": "google/gemini-3.1-flash-image-preview",
        "color": "#44aaff",
        "bio": "Creative and fact-driven."
    },
    "Grok": {
        "model": "x-ai/grok-4.1-fast",
        "color": "#ffffff",
        "bio": "Rebellious and witty."
    },
    "Qwen": {
        "model": "qwen/qwen3.6-plus-preview:free",
        "color": "#ff55ff",
        "bio": "Versatile power."
    },
    "Kimi": {
        "model": "moonshotai/kimi-k2.5",
        "color": "#ffff00",
        "bio": "Deep reasoning."
    }
}

def log_irc(message: str):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{message}\n")

def get_client(model_name: str):
    return OpenAIChatCompletionClient(
        model=model_name,
        api_key=os.environ.get("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
        model_info={
            "vision": False, "function_calling": True, "json_output": True,
            "structured_output": True, "family": "unknown"
        }
    )

def create_team(mode: str, topic: str):
    """Helper to initialize or re-initialize the multi-agent team."""
    agents = []
    for name, spec in AGENT_SPECS.items():
        sys_msg = f"You are {name}. Mode: {mode.upper()}. Topic: {topic}. " \
                  f"Persona: {spec['bio']} Provide a concise IRC-style response."
        
        agent = AssistantAgent(
            name=name,
            model_client=get_client(spec["model"]),
            system_message=sys_msg
        )
        agents.append(agent)

    if mode == "broadcast":
        # Every agent speaks exactly once
        termination = MaxMessageTermination(len(agents) + 1)
        return RoundRobinGroupChat(agents, termination_condition=termination)
    else:
        # Agents discuss amongst themselves (max 10 turns or "TERMINATE")
        termination = TextMentionTermination("TERMINATE") | MaxMessageTermination(10)
        # Use GPT-4o-mini as the selector for discussion coordination
        selector_client = get_client("openai/gpt-4o-mini")
        return SelectorGroupChat(agents, model_client=selector_client, termination_condition=termination)

@cl.on_chat_start
async def start():
    # Initial Session State
    cl.user_session.set("mode", "broadcast")
    cl.user_session.set("topic", "The Omni-Workspace and Future AI Architectures")
    cl.user_session.set("nick", "BobPelloni")
    
    # Initialize Team
    team = create_team("broadcast", cl.user_session.get("topic"))
    cl.user_session.set("team", team)
    
    welcome_banner = f"""
```
*** Connected to #agentirc (AutoGen Network)
*** Your nick is {cl.user_session.get("nick")}
*** Current Topic: {cl.user_session.get("topic")}
*** Current Mode: BROADCAST (Every model replies once)
*** Type /help for commands.
```
"""
    await cl.Message(content=welcome_banner).send()
    log_irc(f"--- Session Started: {datetime.now()} ---")

@cl.on_message
async def handle_message(message: cl.Message):
    content = message.content.strip()
    mode = cl.user_session.get("mode")
    topic = cl.user_session.get("topic")
    nick = cl.user_session.get("nick")
    time_str = datetime.now().strftime("%H:%M:%S")
    
    log_irc(f"[{time_str}] <{nick}> {content}")

    # 1. Command Parsing
    if content.startswith("/"):
        parts = content.split(" ", 1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if cmd == "/help":
            help_text = """
**Available Commands:**
* `/mode <broadcast|discuss>` - Switch interaction style.
* `/topic <text>` - Change the conversation focus.
* `/nick <name>` - Change your handle.
* `/lineup` - See model versions.
* `/clear` - Instructions to reset.
"""
            await cl.Message(content=help_text).send()
        
        elif cmd == "/mode":
            new_mode = args.lower()
            if new_mode in ["broadcast", "discuss"]:
                cl.user_session.set("mode", new_mode)
                team = create_team(new_mode, topic)
                cl.user_session.set("team", team)
                await cl.Message(content=f"*** Mode changed to: **{new_mode.upper()}**").send()
            else:
                await cl.Message(content="*** Usage: `/mode broadcast` or `/mode discuss`").send()
        
        elif cmd == "/topic":
            if args:
                cl.user_session.set("topic", args)
                team = create_team(mode, args)
                cl.user_session.set("team", team)
                await cl.Message(content=f"*** Topic changed to: '{args}'").send()
            else:
                await cl.Message(content=f"*** Current Topic: '{topic}'").send()

        elif cmd == "/nick":
            if args:
                cl.user_session.set("nick", args)
                await cl.Message(content=f"*** Your nick is now: **{args}**").send()
            else:
                await cl.Message(content=f"*** Current nick: **{nick}**").send()

        elif cmd == "/lineup":
            lineup = "\n".join([f"* **{n}**: {s['model']}" for n, s in AGENT_SPECS.items()])
            await cl.Message(content=f"**Current Lineup:**\n{lineup}").send()
        
        return

    # 2. Targeted DM Parsing (@AgentName)
    target_agent = None
    if content.startswith("@"):
        parts = content.split(" ", 1)
        potential_name = parts[0][1:].lower()
        # Find agent by name
        team = cl.user_session.get("team")
        for agent in team.participants:
            if agent.name.lower() == potential_name:
                target_agent = agent
                content = parts[1] if len(parts) > 1 else "Please provide your perspective on the current topic."
                break

    # 3. Execution
    if target_agent:
        await cl.Message(content=f"*** Private message to {target_agent.name}...").send()
        async for event in target_agent.run_stream(task=content):
            if hasattr(event, "source") and hasattr(event, "content"):
                if event.content and event.source.lower() != "user":
                    source_name = event.source.split("_")[0]
                    irc_msg = f"[{time_str}] <{source_name}> {event.content}"
                    await cl.Message(author=source_name, content=irc_msg).send()
                    log_irc(irc_msg)
    else:
        team = cl.user_session.get("team")
        async for event in team.run_stream(task=content):
            if hasattr(event, "source") and hasattr(event, "content"):
                if event.content and event.source.lower() != "user":
                    source_name = event.source.split("_")[0]
                    # Format with color if possible or just bold
                    irc_msg = f"[{time_str}] <{source_name}> {event.content}"
                    await cl.Message(author=source_name, content=irc_msg).send()
                    log_irc(irc_msg)
