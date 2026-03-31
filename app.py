import os
import autogen
import chainlit as cl
from autogen.io.base import IOStream
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1"

# Define the models we want to use
MODELS = {
    "Claude": "anthropic/claude-3.5-sonnet",
    "Gemini": "google/gemini-2.0-flash-001",
    "Grok": "x-ai/grok-2-1212",
    "GPT-4": "openai/gpt-4o"
}

# --- AutoGen x Chainlit Integration ---

def register_agent_callbacks(agents):
    """Register callbacks on agents to send their messages to Chainlit UI."""
    for agent in agents:
        def agent_reply(recipient, messages, sender, config):
            last_msg = messages[-1].get("content", "")
            if last_msg:
                cl.run_sync(cl.Message(content=last_msg, author=sender.name).send())
            return False, None  # Continue with normal reply logic
        
        agent.register_reply(
            [autogen.Agent, None],
            reply_func=agent_reply,
            position=0
        )

# --- Agent Initialization ---

def get_config(model_name: str):
    return [
        {
            "model": model_name,
            "api_key": OPENROUTER_API_KEY,
            "base_url": BASE_URL,
            "api_type": "openai",
        }
    ]

@cl.on_chat_start
async def start():
    # Set the default IOStream to our Chainlit version
    IOStream.set_default(ChainlitIOStream())

    # Create the agents
    agents = []
    for name, model in MODELS.items():
        agent = autogen.AssistantAgent(
            name=name,
            llm_config={
                "config_list": get_config(model),
                "temperature": 0.7,
            },
            system_message=f"You are {name}, an expert AI participating in a group chat. "
                           "Be concise, insightful, and engage directly with the other models and the user. "
                           "Maintain your unique persona and perspective."
        )
        agents.append(agent)

    # The User Proxy handles the interface between the user and the group
    user_proxy = ChainlitUserProxyAgent(
        name="User",
        human_input_mode="NEVER",  # We handle initiation in on_message
        max_consecutive_auto_reply=10,
        is_termination_msg=lambda x: "TERMINATE" in x.get("content", ""),
        code_execution_config=False,
    )

    # Set up the Group Chat
    groupchat = autogen.GroupChat(
        agents=agents + [user_proxy],
        messages=[],
        max_round=12,
        speaker_selection_method="auto"  # The manager will decide who speaks next
    )
    
    manager = autogen.GroupChatManager(
        groupchat=groupchat,
        llm_config={"config_list": get_config("openai/gpt-4o-mini")} # Use a fast model for management
    )

    cl.user_session.set("user_proxy", user_proxy)
    cl.user_session.set("manager", manager)

    await cl.Message(content="Welcome to the AI IRC Room! Claude, Gemini, Grok, and GPT-4o are standing by. Type something to start the discussion.").send()

@cl.on_message
async def handle_message(message: cl.Message):
    user_proxy = cl.user_session.get("user_proxy")
    manager = cl.user_session.get("manager")

    # Run the chat
    await cl.make_async(user_proxy.initiate_chat)(
        manager,
        message=message.content,
    )
