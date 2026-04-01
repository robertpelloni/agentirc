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

# IRC Custom CSS for that 90s terminal feel
IRC_CSS = """
/* Force monospace font globally */
* {
    font-family: 'Courier New', Courier, monospace !important;
}

/* Dark background */
body {
    background-color: #0c0c0c !important;
    color: #00ff00 !important;
}

/* Adjust message containers to look more like a log */
.step-container {
    border-left: 2px solid #333 !important;
    padding-left: 10px !important;
    margin-bottom: 2px !important;
}

/* Style the author name */
.author-name {
    color: #ff00ff !important; /* Classic IRC Magenta */
    font-weight: bold;
}

/* Remove avatars for a cleaner text-only look */
.avatar {
    display: none !important;
}
"""

# --- Configuration ---
# (Rest of specs remain the same...)
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
    },
    "DeepSeek": {
        "model": "deepseek/deepseek-v3.2",
        "system_message": "You are DeepSeek v3.2. Provide a concise response to the user. Engage in the IRC chat."
    }
}

def get_client(model_name: str):
    """Create an OpenRouter-compatible client for the new AutoGen API."""
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
    # Set the IRC style
    await cl.ChatSettings([]).send()
    # Note: Chainlit might not support set_custom_css in all versions, 
    # but we can try to inject it via Message or just rely on config.toml.
    # For now, let's focus on message formatting.

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
```
*** Connected to #agentirc (AutoGen Network)
*** Topic is 'The Future of Intelligence'
*** Users: Claude, GPT_5, Gemini, Grok, Qwen, Kimi, DeepSeek
```
"""
    await cl.Message(content=welcome_banner).send()

@cl.on_message
async def handle_message(message: cl.Message):
    team = cl.user_session.get("team")
    
    # Formatting user message like IRC
    time_str = datetime.now().strftime("%H:%M:%S")
    # Note: We don't resend the user message to Chainlit because it's already there, 
    # but we can format it in the transcript.

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
