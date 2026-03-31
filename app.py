import os
import autogen
import chainlit as cl
from autogen.io.base import IOStream
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1"

# Define the models and their specific personas
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
        "model": "x-ai/grok-2-1212",
        "system_message": "You are Grok. You bring a rebellious, witty edge to the debate. Engage in the IRC chat with other AIs."
    }
}

# --- AutoGen x Chainlit Integration ---

class ChainlitIOStream(IOStream):
    """Redirects AutoGen prints and logs to the Chainlit UI."""
    def print(self, *objects, sep=" ", end="\n", flush=False):
        content = sep.join(map(str, objects))
        if content.strip():
            # Filter internal AutoGen headers to keep the chat clean
            if not any(x in content for x in ["--------------------------------------------------------------------------------", "Next agent:", "using auto-reply"]):
                cl.run_sync(cl.Message(content=content, author="System").send())

class ChainlitUserProxyAgent(autogen.UserProxyAgent):
    """Handles human-in-the-loop interaction via the Chainlit UI."""
    def get_human_input(self, prompt: str) -> str:
        display_prompt = prompt.split(".")[0] + "?" # Simplify the long AutoGen prompt
        
        res = cl.run_sync(cl.AskUserMessage(
            content=f"**User Intervention:** {display_prompt}",
            timeout=600
        ).send())
        
        if res:
            return res['output']
        return ""

def register_agent_callbacks(agents):
    """Register callbacks to display agent-to-agent messages in the UI."""
    for agent in agents:
        def agent_reply(recipient, messages, sender, config):
            last_msg = messages[-1].get("content", "")
            if last_msg:
                cl.run_sync(cl.Message(content=last_msg, author=sender.name).send())
            return False, None
        
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

    # Create the agents with specific personas
    agents = []
    for name, spec in AGENT_SPECS.items():
        agent = autogen.AssistantAgent(
            name=name,
            llm_config={
                "config_list": get_config(spec["model"]),
                "temperature": 0.7,
            },
            system_message=spec["system_message"]
        )
        agents.append(agent)

    # Register UI callbacks
    register_agent_callbacks(agents)

    # The User Proxy allows you to participate or just initiate
    user_proxy = ChainlitUserProxyAgent(
        name="User",
        human_input_mode="ALWAYS", # Allow human-in-the-loop for true IRC feel
        max_consecutive_auto_reply=10,
        is_termination_msg=lambda x: "TERMINATE" in x.get("content", ""),
        code_execution_config=False,
    )
    register_agent_callbacks([user_proxy])

    # Set up the Group Chat
    groupchat = autogen.GroupChat(
        agents=agents + [user_proxy],
        messages=[],
        max_round=15,
        speaker_selection_method="auto"
    )
    
    manager = autogen.GroupChatManager(
        groupchat=groupchat,
        llm_config={"config_list": get_config("openai/gpt-4o-mini")}
    )

    cl.user_session.set("user_proxy", user_proxy)
    cl.user_session.set("manager", manager)

    await cl.Message(content="**AI IRC Room Activated.**\nClaude, GPT, Gemini, and Grok are in the channel. Send a message to start the debate.").send()

@cl.on_message
async def handle_message(message: cl.Message):
    user_proxy = cl.user_session.get("user_proxy")
    manager = cl.user_session.get("manager")

    # Kick off the group chat
    await cl.make_async(user_proxy.initiate_chat)(
        manager,
        message=message.content,
        clear_history=False # Keep context across turns like a real IRC chat
    )
