import os
import asyncio
import chainlit as cl
from datetime import datetime
from dotenv import load_dotenv

# --- Python 3.14 Compatibility Patch ---
import anyio.to_thread
import typing

async def patched_run_sync(func: typing.Callable, *args, **kwargs):
    # Ignore anyio-specific kwargs like limiter or abandon_on_cancel
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

# --- Configuration ---
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1"

# Define the models and their personas
AGENT_SPECS = {
    "Claude": {
        "model": "anthropic/claude-sonnet-4.6",
        "system_message": "You are Claude 4.6. Provide a concise response to the user. Engage in the IRC chat."
    },
    "GPT_5": {
        "model": "openai/gpt-5.4-mini",
        "system_message": "You are GPT-5.4-mini. Provide a concise response to the user. Engage in the IRC chat."
    },
    "Gemini": {
        "model": "google/gemini-3.1-flash-image-preview",
        "system_message": "You are Gemini 3.1. Provide a concise response to the user. Engage in the IRC chat."
    },
    "Grok": {
        "model": "x-ai/grok-4.1-fast",
        "system_message": "You are Grok 4.1-fast. Provide a concise response to the user. Engage in the IRC chat."
    },
    "Qwen": {
        "model": "qwen/qwen3.6-plus-preview:free",
        "system_message": "You are Qwen 3.6 Plus. Provide a concise response to the user. Engage in the IRC chat."
    },
    "Kimi": {
        "model": "moonshotai/kimi-k2.5",
        "system_message": "You are Kimi K2.5. Provide a concise response to the user. Engage in the IRC chat."
    }
}

def get_client(model_name: str):
    """Create an OpenRouter-compatible client for the new AutoGen API."""
    return OpenAIChatCompletionClient(
        model=model_name,
        api_key=OPENROUTER_API_KEY,
        base_url=BASE_URL,
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
    # 1. Initialize the agents
    agents = []
    for name, spec in AGENT_SPECS.items():
        agent = AssistantAgent(
            name=name,
            model_client=get_client(spec["model"]),
            system_message=spec["system_message"]
        )
        agents.append(agent)

    # 2. Define termination condition: Stop after everyone has spoken once (User + N agents)
    termination = MaxMessageTermination(len(agents) + 1)

    # 3. Create the IRC Team (RoundRobin ensures every agent gets exactly one turn)
    team = RoundRobinGroupChat(
        agents, 
        termination_condition=termination
    )

    cl.user_session.set("team", team)
    
    # Welcome banner
    welcome_banner = """
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
    await cl.Message(content=welcome_banner).send()

@cl.on_message
async def handle_message(message: cl.Message):
    team = cl.user_session.get("team")

    # Use run_stream to capture agent-to-agent interactions
    async for event in team.run_stream(task=message.content):
        if hasattr(event, "source") and hasattr(event, "content"):
            if event.content and event.source.lower() != "user":
                # Clean the source name
                source_name = event.source.split("_")[0]
                time_str = datetime.now().strftime("%H:%M:%S")
                
                # Full IRC format: [TIMESTAMP] <NICK> MESSAGE
                irc_msg = f"[{time_str}] <{source_name}> {event.content}"
                
                await cl.Message(
                    author=source_name,
                    content=irc_msg
                ).send()
