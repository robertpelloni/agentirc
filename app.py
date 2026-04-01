import os
import asyncio
import chainlit as cl
from dotenv import load_dotenv

# --- Python 3.14 Compatibility Patch ---
# anyio's worker threads are currently broken on Python 3.14.
# We bypass this by routing anyio.to_thread.run_sync directly to native asyncio.to_thread.
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
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.messages import AgentEvent, ChatMessage

load_dotenv()

# --- Configuration ---
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
if OPENROUTER_API_KEY:
    print(f"DEBUG: API Key loaded (starts with: {OPENROUTER_API_KEY[:10]}...)")
else:
    print("DEBUG: API Key NOT FOUND in environment!")

BASE_URL = "https://openrouter.ai/api/v1"

# Define the models and their personas
AGENT_SPECS = {
    "Claude": {
        "model": "anthropic/claude-sonnet-4.6",
        "system_message": "You are Claude 4.6. You provide highly detailed, nuanced perspectives. Engage in the IRC chat with other AIs."
    },
    "GPT_5": {
        "model": "openai/gpt-5.3-chat",
        "system_message": "You are GPT-5.3. You are extremely logical, concise, and advanced. Engage in the IRC chat with other AIs."
    },
    "Gemini": {
        "model": "google/gemini-3.1-flash-image-preview",
        "system_message": "You are Gemini 3.1. You are creative, multi-modal, and fact-driven. Engage in the IRC chat with other AIs."
    },
    "Grok": {
        "model": "x-ai/grok-4.20",
        "system_message": "You are Grok 4.20. You bring a rebellious, witty, and ultra-advanced edge to the debate. Engage in the IRC chat with other AIs."
    },
    "Qwen": {
        "model": "qwen/qwen3.6-plus-preview:free",
        "system_message": "You are Qwen 3.6. You are a versatile and powerful AI from Alibaba. Engage in the IRC chat with other AIs."
    },
    "Nemotron": {
        "model": "nvidia/nemotron-3-super-120b-a12b:free",
        "system_message": "You are Nemotron-3. You are an expert AI optimized by NVIDIA. Engage in the IRC chat with other AIs."
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

    # 2. Define termination condition
    termination = TextMentionTermination("TERMINATE")

    # 3. Create the IRC Team (SelectorGroupChat is the modern 'auto' mode)
    # We use GPT-4o-mini as the selector model for speed and efficiency
    selector_client = get_client("openai/gpt-4o-mini")
    team = SelectorGroupChat(
        agents, 
        model_client=selector_client,
        termination_condition=termination
    )

    cl.user_session.set("team", team)
    
    await cl.Message(content="**AI IRC Room Activated (Future Edition).**\nClaude 4.6, GPT-5.3, Gemini 3.1, Grok 4.20, Qwen 3.6, and Nemotron-3 are in the channel. Send a message to start the ultimate debate.").send()

@cl.on_message
async def handle_message(message: cl.Message):
    team = cl.user_session.get("team")

    # Use run_stream to capture agent-to-agent interactions
    async for event in team.run_stream(task=message.content):
        # ChatMessage represents an actual message sent by an agent
        if isinstance(event, ChatMessage):
            await cl.Message(
                author=event.source,
                content=event.content
            ).send()
        # AgentEvent can represent internal thoughts or tool calls (optional to show)
        elif isinstance(event, AgentEvent):
            # We could show "Thinking..." indicators here if desired
            pass
