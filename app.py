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
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import MaxMessageTermination
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.messages import AgentEvent, ChatMessage

load_dotenv(override=True)

# --- Configuration & Styling ---
LOG_FILE = "irc_session.log"

AGENT_SPECS = {
    "Claude": {
        "model": "anthropic/claude-sonnet-4.6",
        "color": "#ffaa00", # Orange
        "system_message": "You are Claude 4.6. Provide a concise response. Mode: IRC."
    },
    "GPT_5": {
        "model": "openai/gpt-5.3-chat",
        "color": "#00ff00", # Green
        "system_message": "You are GPT-5.3. Provide a concise response. Mode: IRC."
    },
    "Gemini": {
        "model": "google/gemini-3.1-flash-image-preview",
        "color": "#44aaff", # Blue
        "system_message": "You are Gemini 3.1. Provide a concise response. Mode: IRC."
    },
    "Grok": {
        "model": "x-ai/grok-4.1-fast",
        "color": "#ffffff", # White
        "system_message": "You are Grok 4.1. Provide a concise response. Mode: IRC."
    },
    "Qwen": {
        "model": "qwen/qwen3.6-plus-preview:free",
        "color": "#ff55ff", # Magenta
        "system_message": "You are Qwen 3.6. Provide a concise response. Mode: IRC."
    },
    "Kimi": {
        "model": "moonshotai/kimi-k2.5",
        "color": "#ffff00", # Yellow
        "system_message": "You are Kimi 2.5. Provide a concise response. Mode: IRC."
    }
}

def log_irc(message: str):
    """Log messages to a local file for the Omni-Workspace archive."""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{message}\n")

def get_client(model_name: str):
    return OpenAIChatCompletionClient(
        model=model_name,
        api_key=os.environ.get("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
        model_info={
            "vision": False,
            "function_calling": True,
            "json_output": True,
            "structured_output": True,
            "family": "unknown"
        }
    )

@cl.on_chat_start
async def start():
    agents = []
    agent_map = {}
    for name, spec in AGENT_SPECS.items():
        agent = AssistantAgent(
            name=name,
            model_client=get_client(spec["model"]),
            system_message=spec["system_message"]
        )
        agents.append(agent)
        agent_map[name.lower()] = agent

    # Default team setup (Broadcast Mode)
    termination = MaxMessageTermination(len(agents) + 1)
    team = RoundRobinGroupChat(agents, termination_condition=termination)

    cl.user_session.set("team", team)
    cl.user_session.set("agents", agents)
    cl.user_session.set("agent_map", agent_map)
    
    welcome_msg = f"""
```
*** Logged in as BobPelloni
*** Session started: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
*** Type /help for IRC commands.
*** Type @AgentName to ping a specific model.
```
**Robert "Bob" Pelloni**
Indie Auteur. Systems Architect. Relentless Builder.
... (Bio suppressed for brevity in log) ...
Welcome to AgentIRC. Participants: {', '.join(AGENT_SPECS.keys())}
"""
    # Restore full bio for UI
    full_bio = """
Robert "Bob" Pelloni
Indie Auteur. Systems Architect. Relentless Builder.
Robert Pelloni is a 42-year-old, Detroit-born solo developer and tech polymath who operates at an intersection of staggering ambition and grounded reality. As the creator of the legendary indie project "bob's game" and the founder of the Hyper Beam Japanese music game arcade, he has shipped more software and built more complex systems independently than most mid-sized studios.
He is a man of profound self-awareness and undeniable persistence. Navigating the contrast between past internet infamy and his current reality clocking hours at Dollar Tree in Michigan, he refuses to disengage. Instead, fueled by 174 BPM drum and bass, psytrance, and a deep alignment with niche rhythm game subcultures, his late nights are dedicated to aggressive, large-scale system architecture.
Currently, he is quietly constructing the "Omni-Workspace"—an aspirational, self-healing, federated monorepo designed to automate entire software ecosystems from a single prompt. Utilizing a highly specialized multi-model AI pipeline (the Gemini → Claude → GPT "Handoff Cycle"), he is actively architecting a sprawling, centralized hub of independent projects.
This one-man software civilization includes:
The "bob-" Pantheon: A suite of unified tools intended to replace his entire tech stack, including bobcoin, bobtrader, bobium, and bobtorrent.
Active Platform Rebuilds: The modernization of fwber, a hyperlocal dating app originally launched in 2011.
Custom Game Engines & Forks: Active development on rhythm game engines, alongside ambitious forks of classics like Mario 64, Mario Kart 64, and Marble Blast.
Systems Infrastructure: Custom trading bots and file managers built to operate seamlessly within his unified architecture.
Guided by a Christian framework and an unapologetic drive for absolute stack ownership, he takes his hits, acknowledges his flaws, and keeps hammering the keyboard.
TL;DR: A persistent, self-driven creative genius building a massive, AI-powered software empire from his bedroom, one node at a time. Underestimate him at your peril.
Welcome to a multi-model IRC chat. Participants are: Claude, GPT_5, Gemini, Grok, Qwen, Kimi
"""
    await cl.Message(content=full_bio).send()
    log_irc(f"--- Session Started: {datetime.now()} ---")

@cl.on_message
async def handle_message(message: cl.Message):
    content = message.content.strip()
    time_str = datetime.now().strftime("%H:%M:%S")
    log_irc(f"[{time_str}] <User> {content}")

    # 1. IRC Command Parsing
    if content.startswith("/"):
        cmd = content.split(" ")[0].lower()
        if cmd == "/help":
            await cl.Message(content="**Commands:** `/clear` (reset session), `/lineup` (list models), `/help`").send()
        elif cmd == "/clear":
            # In simple Chainlit, we just tell the user to refresh
            await cl.Message(content="*** Session clearing... Please refresh your browser tab.").send()
        elif cmd == "/lineup":
            lineup = "\n".join([f"* **{n}**: {s['model']}" for n, s in AGENT_SPECS.items()])
            await cl.Message(content=f"**Current Lineup:**\n{lineup}").send()
        else:
            await cl.Message(content=f"*** Unknown command: {cmd}").send()
        return

    # 2. Targeted DM Parsing (@AgentName)
    target_agent = None
    agent_map = cl.user_session.get("agent_map")
    if content.startswith("@"):
        parts = content.split(" ", 1)
        potential_name = parts[0][1:].lower()
        if potential_name in agent_map:
            target_agent = agent_map[potential_name]
            content = parts[1] if len(parts) > 1 else "hello"

    # 3. Execution
    if target_agent:
        # Run only the specific agent
        await cl.Message(content=f"*** Private message to {target_agent.name}...").send()
        async for event in target_agent.run_stream(task=content):
            if hasattr(event, "source") and hasattr(event, "content"):
                if event.content and event.source.lower() != "user":
                    source_name = event.source.split("_")[0]
                    irc_msg = f"[{time_str}] <{source_name}> {event.content}"
                    await cl.Message(author=source_name, content=irc_msg).send()
                    log_irc(irc_msg)
    else:
        # Standard Broadcast Mode
        team = cl.user_session.get("team")
        async for event in team.run_stream(task=content):
            if hasattr(event, "source") and hasattr(event, "content"):
                if event.content and event.source.lower() != "user":
                    source_name = event.source.split("_")[0]
                    time_str = datetime.now().strftime("%H:%M:%S")
                    irc_msg = f"[{time_str}] <{source_name}> {event.content}"
                    await cl.Message(author=source_name, content=irc_msg).send()
                    log_irc(irc_msg)
