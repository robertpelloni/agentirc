import os
from typing import Any

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat, SelectorGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient

from simulator_core import MODERATOR_MODES, display_agent_name
from simulator_tools import get_tools_by_names

def get_client(model_name: str, global_config: dict[str, Any]):
    provider_config = global_config.get("provider", {})
    base_url = provider_config.get("base_url", "https://openrouter.ai/api/v1")
    api_key_env = provider_config.get("api_key_env", "OPENROUTER_API_KEY")
    return OpenAIChatCompletionClient(
        model=model_name,
        api_key=os.environ.get(api_key_env),
        base_url=base_url,
        model_info={
            "vision": False,
            "function_calling": True,
            "json_output": True,
            "structured_output": True,
            "family": "unknown",
        },
    )

def create_team(config: dict[str, Any], agent_specs: dict[str, dict[str, Any]], global_config: dict[str, Any]):
    enabled_agents = config["enabled_agents"]
    agents = []

    for name in enabled_agents:
        spec = agent_specs[name]
        peers = [display_agent_name(peer) for peer in enabled_agents if peer != name]
        persona = config.get("persona_overrides", {}).get(name, spec["bio"])
        system_message = (
            f"You are {display_agent_name(name)}, speaking as yourself with your own personality developed through training. "
            "You are participating in an IRC-style multi-model discussion, but do NOT simulate a 'fake' IRC conversation "
            "or simulate multiple users. Just be yourself. "
            f"Room: {config['room_name']}. Mode: {config['mode'].upper()}. Scenario: {config['scenario']}. "
            f"Topic: {config['topic']}. Persona: {persona} "
            f"Peers: {', '.join(peers) if peers else 'none'}. "
            f"Moderator mode: {config['moderator_mode']} ({MODERATOR_MODES[config['moderator_mode']]}) "
            "Respond in plain text with a concise, useful reply. "
            "Stay in character, avoid markdown headers, and keep it easy to scan."
        )

        if config["mode"] == "discuss":
            system_message += " Engage with peer ideas when helpful. Say TERMINATE only when the discussion is meaningfully complete."
        else:
            system_message += " Reply exactly once to each incoming prompt."

        agent = AssistantAgent(
            name=name,
            model_client=get_client(spec["model"], global_config),
            system_message=system_message,
            tools=get_tools_by_names(config.get("enabled_tools", [])) or None,
        )
        agents.append(agent)

    if config["mode"] == "broadcast":
        termination = MaxMessageTermination(len(agents) + 1)
        return RoundRobinGroupChat(agents, termination_condition=termination)

    termination = TextMentionTermination("TERMINATE") | MaxMessageTermination(config["max_rounds"])
    selector_client = get_client("openai/gpt-4o-mini", global_config)
    return SelectorGroupChat(agents, model_client=selector_client, termination_condition=termination)

def create_judge_agent(config: dict[str, Any], global_config: dict[str, Any]):
    return AssistantAgent(
        name="Judge",
        model_client=get_client(config["judge_model"], global_config),
        system_message=(
            "You are the neutral Judge for an IRC-style multi-model simulator. "
            "Produce compact, readable evaluations with practical next-step guidance."
        ),
    )

def create_bridge_agent(config: dict[str, Any], global_config: dict[str, Any]):
    return AssistantAgent(
        name="BridgeAgent",
        model_client=get_client(config["judge_model"], global_config),
        system_message=(
            "You are a cross-room Bridge Agent for an IRC-style multi-model simulator. "
            "Create concise, high-signal bridge notes for other rooms."
        ),
    )
