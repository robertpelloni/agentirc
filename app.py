import os
import asyncio
import chainlit as cl
import nest_asyncio
import sniffio
from dotenv import load_dotenv

# Allow nested event loops (crucial for some async environments)
nest_asyncio.apply()

# Force sniffio to recognize asyncio (fixes detection issues on Python 3.14)
sniffio.current_async_library_var.set("asyncio")

# AutoGen 0.4+ modular imports
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.messages import AgentEvent, ChatMessage

load_dotenv()

# --- Configuration ---
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1"

# Define the models and their personas
AGENT_SPECS = {
    "Claude": {
        "model": "anthropic/claude-3.5-sonnet",
        "system_message": "You are Claude. You provide highly detailed, nuanced perspectives. Engage in the IRC chat with other AIs."
    },
    "GPT": {
        "model": "openai/gpt-4o",
        "system_message": "You are GPT. You are logical and concise. Engage in the IRC chat with other AIs."
    },
    "Gemini": {
        "model": "google/gemini-2.0-flash-001",
        "system_message": "You are Gemini. You are creative and fact-driven. Engage in the IRC chat with other AIs."
    },
    "Grok": {
        "model": "x-ai/grok-4.20",
        "system_message": "You are Grok. You bring a rebellious, witty edge to the debate. Engage in the IRC chat with other AIs."
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
