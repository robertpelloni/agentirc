import argparse
import asyncio
import os
import sys
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pr_review")

# Setup for standalone testing or integration
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from services.agents import get_agent_specs, get_client
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from simulator_tools import TOOL_CATALOG

# Mock function for fetching a PR diff (can be replaced with actual tool later)
async def fetch_github_pr(url: str) -> str:
    """Fetches a PR diff from GitHub."""
    return f"Mock PR Diff for {url}\n+ def new_feature():\n+     return True\n- def old_feature():\n-     return False"

async def review_pr(pr_url: str):
    logger.info(f"Starting PR review for {pr_url}")

    specs = get_agent_specs()
    # Find active models, assume we have at least one valid config for testing
    enabled_specs = [s for s in specs.values() if s.get("enabled", True)]

    if not enabled_specs:
        logger.error("No enabled models found in agent_specs.json")
        return

    # Use the first available model for all roles for simplicity in this scaffold
    base_spec = enabled_specs[0]
    model_name = base_spec["name"]
    base_url = base_spec.get("base_url")
    client = get_client(model_name, base_url)

    # Define personas
    personas = {
        "Code_Critic": "You are a harsh but fair code critic. You look for inefficiencies, code smells, and poor naming conventions.",
        "Security_Auditor": "You are a paranoid security auditor. You look for vulnerabilities, injection flaws, and insecure dependencies.",
        "QA_Engineer": "You are a meticulous QA engineer. You look for missing tests, edge cases, and logic bugs.",
        "Tech_Lead": "You are the pragmatic Tech Lead. You guide the discussion, summarize the findings, and make the final decision to approve or reject. End your summary with 'CONSENSUS_REACHED'."
    }

    agents = []
    for name, system_message in personas.items():
        agent = AssistantAgent(
            name=name,
            model_client=client,
            system_message=system_message,
            tools=[fetch_github_pr] if name == "Tech_Lead" else [] # Give Tech Lead the tool
        )
        agents.append(agent)

    text_termination = TextMentionTermination("CONSENSUS_REACHED")
    max_message_termination = MaxMessageTermination(max_messages=10)
    termination = text_termination | max_message_termination

    team = SelectorGroupChat(
        participants=agents,
        model_client=client,
        termination_condition=termination
    )

    prompt = f"Please review the pull request at {pr_url}. Tech_Lead, please fetch the PR diff and coordinate the review."

    logger.info("Swarm initialized. Starting discussion...")

    # Run the swarm
    async for event in team.run_stream(task=prompt):
        if hasattr(event, "source") and hasattr(event, "content"):
            logger.info(f"[{event.source}] {event.content}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GitHub PR Review Agents")
    parser.add_argument("url", type=str, help="GitHub PR URL")
    args = parser.parse_args()

    try:
        asyncio.run(review_pr(args.url))
    except KeyboardInterrupt:
        logger.info("Review cancelled.")
