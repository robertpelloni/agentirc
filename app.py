import os
import asyncio
import chainlit as cl
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
from autogen_agentchat.conditions import MaxMessagesTermination
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
        "model": "openai/gpt-5.3-chat",
        "system_message": "You are GPT-5.3. Provide a concise response to the user. Engage in the IRC chat."
    },
    "Gemini": {
        "model": "google/gemini-3.1-flash-image-preview",
        "system_message": "You are Gemini 3.1. Provide a concise response to the user. Engage in the IRC chat."
    },
    "Grok": {
        "model": "x-ai/grok-4.20",
        "system_message": "You are Grok 4.20. Provide a concise response to the user. Engage in the IRC chat."
    },
    "Qwen": {
        "model": "qwen/qwen3.6-plus-preview:free",
        "system_message": "You are Qwen 3.6 Plus. Provide a concise response to the user. Engage in the IRC chat."
    },
    "Nemotron": {
        "model": "nvidia/nemotron-3-super-120b-a12b:free",
        "system_message": "You are Nemotron-3. Provide a concise response to the user. Engage in the IRC chat."
    }
}

def get_client(model_name: str):
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
    agents = []
    for name, spec in AGENT_SPECS.items():
        agent = AssistantAgent(
            name=name,
            model_client=get_client(spec["model"]),
            system_message=spec["system_message"]
        )
        agents.append(agent)

    # Stop after every agent has spoken once + User message
    termination = MaxMessagesTermination(len(agents) + 1)

    team = RoundRobinGroupChat(
        agents, 
        termination_condition=termination
    )

    cl.user_session.set("team", team)
    
    if OPENROUTER_API_KEY:
        print(f"DEBUG: API Key loaded (starts with: {OPENROUTER_API_KEY[:10]}...)")
    else:
        print("DEBUG: API Key NOT FOUND!")

    await cl.Message(content="**AI IRC Room: Broadcast Mode.**\nClaude, GPT-5, Gemini, Grok, Qwen, and Nemotron will respond to your messages. Type a prompt to begin.").send()

@cl.on_message
async def handle_message(message: cl.Message):
    team = cl.user_session.get("team")

    async for event in team.run_stream(task=message.content):
        if hasattr(event, "source") and hasattr(event, "content"):
            if event.content and event.source.lower() != "user":
                source_name = event.source.split("_")[0]
                await cl.Message(
                    author=source_name,
                    content=f"**{source_name}**: {event.content}"
                ).send()
