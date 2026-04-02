import os
import asyncio
import chainlit as cl
from datetime import datetime
from dotenv import load_dotenv
import io
import random

# PDF generation imports
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER

# --- Python 3.14 Compatibility Patch ---
import anyio.to_thread
import typing

async def patched_run_sync(func: typing.Callable, *args, **kwargs):
    kwargs.pop("limiter", None)
    kwargs.pop("abandon_on_cancel", None)
    return await asyncio.to_thread(func, *args, **kwargs)

anyio.to_thread.run_sync = patched_run_sync
# ---------------------------------------

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.conditions import MaxMessageTermination
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.messages import AgentEvent, ChatMessage

load_dotenv(override=True)

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1"

AGENT_SPECS = {
    "Claude": {
        "model": "anthropic/claude-sonnet-4.6",
        "system_message": "You are Claude 4.6. Provide a concise response. Engage in the IRC chat. ALWAYS use Markdown."
    },
    "GPT_5": {
        "model": "openai/gpt-5.4-mini",
        "system_message": "You are GPT-5.4-mini. Provide a concise response. Engage in the IRC chat. ALWAYS use Markdown."
    },
    "Gemini": {
        "model": "google/gemini-3.1-flash-image-preview",
        "system_message": "You are Gemini 3.1. Provide a concise response. Engage in the IRC chat. ALWAYS use Markdown."
    },
    "Grok": {
        "model": "x-ai/grok-4.1-fast",
        "system_message": "You are Grok 4.1-fast. Provide a concise response. Engage in the IRC chat. ALWAYS use Markdown."
    },
    "Qwen": {
        "model": "qwen/qwen3.6-plus-preview:free",
        "system_message": "You are Qwen 3.6 Plus. Provide a concise response. Engage in the IRC chat. ALWAYS use Markdown."
    },
    "Kimi": {
        "model": "moonshotai/kimi-k2.5",
        "system_message": "You are Kimi K2.5. Provide a concise response. Engage in the IRC chat. ALWAYS use Markdown."
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
    cl.user_session.set("chat_history", [])
    
    agents = []
    for name, spec in AGENT_SPECS.items():
        agent = AssistantAgent(
            name=name,
            model_client=get_client(spec["model"]),
            system_message=spec["system_message"]
        )
        agents.append(agent)

    termination = MaxMessageTermination(len(agents) + 1)
    team = RoundRobinGroupChat(agents, termination_condition=termination)
    cl.user_session.set("team", team)
    cl.user_session.set("agents", agents)
    
    welcome_banner = """
# Robert "Bob" Pelloni
### Indie Auteur. Systems Architect. Relentless Builder.

Welcome to the **AgentIRC** hub. This is a multi-model real-time interaction environment.

---
**Available Convenience Features:**
*   **Export MD:** Get the full transcript in clean Markdown.
*   **Export PDF:** Professional document export for your sessions.
*   **Spontaneous Debate:** Trigger a random topic discussion among the agents.
"""
    actions = [
        cl.Action(name="export_md", label="Export MD", value="md"),
        cl.Action(name="export_pdf", label="Export PDF", value="pdf"),
        cl.Action(name="trigger_debate", label="Spontaneous Debate", value="debate")
    ]
    await cl.Message(content=welcome_banner, actions=actions).send()

@cl.action_callback("trigger_debate")
async def on_trigger_debate(action):
    topics = [
        "The future of AGI and its impact on indie developers.",
        "Is the simulation hypothesis scientifically testable?",
        "The cultural significance of drum and bass in the 21st century.",
        "Should AI have its own version of the Turing test for humans?",
        "The architectural merits of monolithic vs. federated repos."
    ]
    topic = random.choice(topics)
    await cl.Message(content=f"🚀 **Topic Selected:** *{topic}*").send()
    
    # We trigger a message as if the user asked
    await handle_message(cl.Message(content=f"Discuss this topic: {topic}"))

@cl.action_callback("export_md")
async def on_export_md(action):
    history = cl.user_session.get("chat_history")
    if not history:
        await cl.Message(content="No chat history to export yet!").send()
        return

    md_content = "# AgentIRC Chat Export\n\n"
    for msg in history:
        md_content += f"**[{msg['time']}]** `<{msg['author']}>` {msg['content']}\n\n"

    file_bytes = md_content.encode("utf-8")
    await cl.Message(content="Here is your Markdown export:").send()
    await cl.File(content=file_bytes, name=f"AgentIRC_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md").send()

@cl.action_callback("export_pdf")
async def on_export_pdf(action):
    history = cl.user_session.get("chat_history")
    if not history:
        await cl.Message(content="No chat history to export yet!").send()
        return

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=LETTER)
    styles = getSampleStyleSheet()
    
    # Custom style for agent names
    agent_style = ParagraphStyle(
        'AgentStyle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        spaceAfter=2
    )
    
    story = []
    story.append(Paragraph("AgentIRC Chat Export", styles['Title']))
    story.append(Paragraph(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Italic']))
    story.append(Spacer(1, 0.2*inch))

    for msg in history:
        header = f"<b>[{msg['time']}]</b> &lt;{msg['author']}&gt;"
        story.append(Paragraph(header, agent_style))
        content = msg['content'].replace('\n', '<br/>')
        story.append(Paragraph(content, styles['Normal']))
        story.append(Spacer(1, 0.15*inch))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    await cl.Message(content="Here is your PDF export:").send()
    await cl.File(content=pdf_bytes, name=f"AgentIRC_Export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf").send()

@cl.on_message
async def handle_message(message: cl.Message):
    team = cl.user_session.get("team")
    history = cl.user_session.get("chat_history")
    
    time_str = datetime.now().strftime("%H:%M:%S")
    history.append({"time": time_str, "author": "User", "content": message.content})

    async for event in team.run_stream(task=message.content):
        if hasattr(event, "source") and hasattr(event, "content"):
            if event.content and event.source.lower() != "user":
                source_name = event.source.split("_")[0]
                time_str = datetime.now().strftime("%H:%M:%S")
                
                history.append({"time": time_str, "author": source_name, "content": event.content})
                
                irc_msg = f"**[{time_str}]** `<{source_name}>` {event.content}"
                
                await cl.Message(
                    author=source_name,
                    content=irc_msg
                ).send()
    
    cl.user_session.set("chat_history", history)
