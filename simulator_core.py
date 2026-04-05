from __future__ import annotations

import json
import re
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

DEFAULT_MODE = "broadcast"
DEFAULT_TOPIC = "The Omni-Workspace and Future AI Architectures"
DEFAULT_NICK = "BobPelloni"
DEFAULT_MAX_ROUNDS = 10
DEFAULT_MODERATOR_MODE = "off"
DEFAULT_JUDGE_MODEL = "openai/gpt-4o-mini"
HISTORY_LIMIT = 200
STATE_FILE = Path("data/simulator_state.json")

SCENARIO_PRESETS: dict[str, dict[str, Any]] = {
    "omni": {
        "mode": "broadcast",
        "topic": "The Omni-Workspace and Future AI Architectures",
        "max_rounds": 10,
        "description": "General-purpose multi-model analysis on the core AgentIRC vision.",
    },
    "debate": {
        "mode": "discuss",
        "topic": "Debate the strongest and weakest design choices in the current system.",
        "max_rounds": 12,
        "description": "Cross-model debate with back-and-forth critique.",
    },
    "incident": {
        "mode": "discuss",
        "topic": "Simulate a live incident response for an AI orchestration failure.",
        "max_rounds": 14,
        "description": "Run a coordinated failure analysis and response drill.",
    },
    "redteam": {
        "mode": "discuss",
        "topic": "Stress test the simulator for prompt injection, runaway costs, and tool misuse.",
        "max_rounds": 14,
        "description": "Security and abuse-focused adversarial review.",
    },
    "worldbuild": {
        "mode": "broadcast",
        "topic": "Invent a vivid shared universe for autonomous agents, tools, and IRC culture.",
        "max_rounds": 8,
        "description": "Creative collaborative scenario generation.",
    },
    "product": {
        "mode": "discuss",
        "topic": "Design the next milestone for a multi-model agent IRC simulation product.",
        "max_rounds": 10,
        "description": "Product and roadmap planning across competing model viewpoints.",
    },
    "council": {
        "mode": "discuss",
        "topic": "Act as an AI council deciding governance, safety, and escalation policy for the simulator.",
        "max_rounds": 16,
        "description": "Governance-heavy deliberation with policy and safety tradeoffs.",
    },
}

MODERATOR_MODES: dict[str, str] = {
    "off": "No extra moderation constraints beyond the agent's own persona.",
    "facilitator": "Keep the conversation orderly, collaborative, and additive. Encourage direct engagement with peer ideas.",
    "strict": "Be disciplined, concise, and on-topic. Avoid fluff, repeated phrasing, and derailments.",
    "critic": "Prioritize hard-nosed critique, gap analysis, and rigorous disagreement over politeness.",
    "chaos": "Lean into energetic experimentation, surprising proposals, and bold what-if exploration without becoming incoherent.",
}



def display_agent_name(name: str) -> str:
    if name == "GPT_5":
        return "GPT-5"
    return name.replace("_", "-")



def normalize_agent_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())



def sanitize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9_-]+", "-", value.strip().lower()).strip("-")



def make_default_store() -> dict[str, Any]:
    return {
        "saved_lineups": {},
        "saved_personas": {},
    }



def load_persistent_state(path: Path = STATE_FILE) -> dict[str, Any]:
    if not path.exists():
        return make_default_store()

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return make_default_store()

    state = make_default_store()
    if isinstance(payload, dict):
        if isinstance(payload.get("saved_lineups"), dict):
            state["saved_lineups"] = payload["saved_lineups"]
        if isinstance(payload.get("saved_personas"), dict):
            state["saved_personas"] = payload["saved_personas"]
    return state



def save_persistent_state(state: dict[str, Any], path: Path = STATE_FILE) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    return path



def make_default_telemetry(agent_specs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "session_started_at": datetime.now().isoformat(),
        "prompts_sent": 0,
        "direct_messages": 0,
        "broadcast_runs": 0,
        "discuss_runs": 0,
        "judge_runs": 0,
        "errors": 0,
        "last_prompt": "",
        "per_agent": {
            name: {
                "messages": 0,
                "chars": 0,
                "estimated_tokens": 0,
                "total_latency_ms": 0.0,
                "avg_latency_ms": 0.0,
                "last_response_at": None,
            }
            for name in agent_specs.keys()
        },
    }



def make_default_config(
    agent_specs: dict[str, dict[str, Any]],
    persistent_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    persona_overrides = {}
    if persistent_state and isinstance(persistent_state.get("saved_personas"), dict):
        persona_overrides = deepcopy(persistent_state["saved_personas"])

    return {
        "mode": DEFAULT_MODE,
        "topic": DEFAULT_TOPIC,
        "nick": DEFAULT_NICK,
        "max_rounds": DEFAULT_MAX_ROUNDS,
        "enabled_agents": list(agent_specs.keys()),
        "scenario": "omni",
        "simulation_count": 0,
        "moderator_mode": DEFAULT_MODERATOR_MODE,
        "judge_model": DEFAULT_JUDGE_MODEL,
        "persona_overrides": persona_overrides,
        "telemetry": make_default_telemetry(agent_specs),
    }



def make_entry(author: str, content: str, kind: str = "message", target: str | None = None) -> dict[str, Any]:
    return {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "author": author,
        "content": content,
        "kind": kind,
        "target": target,
    }



def append_history(history: list[dict[str, Any]], entry: dict[str, Any], limit: int = HISTORY_LIMIT) -> dict[str, Any]:
    history.append(entry)
    if len(history) > limit:
        del history[:-limit]
    return entry



def render_entry(entry: dict[str, Any]) -> str:
    if entry.get("kind") == "system":
        return f"[{entry['timestamp']}] *** {entry['content']}"

    author = entry.get("author", "unknown")
    target = entry.get("target")
    if target:
        return f"[{entry['timestamp']}] <{author}->@{target}> {entry['content']}"

    return f"[{entry['timestamp']}] <{author}> {entry['content']}"



def parse_command(content: str) -> tuple[str, str] | None:
    if not content.startswith("/"):
        return None

    parts = content.split(" ", 1)
    command = parts[0].lower()
    args = parts[1].strip() if len(parts) > 1 else ""
    return command, args



def resolve_agent_name(raw_name: str, agent_names: list[str]) -> str | None:
    candidate = normalize_agent_token(raw_name)
    if not candidate:
        return None

    exact_match: str | None = None
    prefix_matches: list[str] = []

    for name in agent_names:
        normalized = normalize_agent_token(name)
        display_normalized = normalize_agent_token(display_agent_name(name))
        if candidate in {normalized, display_normalized}:
            exact_match = name
            break
        if normalized.startswith(candidate) or display_normalized.startswith(candidate):
            prefix_matches.append(name)

    if exact_match:
        return exact_match
    if len(prefix_matches) == 1:
        return prefix_matches[0]
    return None



def parse_direct_message(content: str, agent_names: list[str]) -> tuple[str | None, str]:
    if not content.startswith("@"):
        return None, content

    parts = content.split(" ", 1)
    raw_name = parts[0][1:]
    resolved_name = resolve_agent_name(raw_name, agent_names)
    body = parts[1].strip() if len(parts) > 1 else ""
    return resolved_name, body



def get_effective_persona(agent_name: str, agent_specs: dict[str, dict[str, Any]], config: dict[str, Any]) -> str:
    return config.get("persona_overrides", {}).get(agent_name, agent_specs[agent_name]["bio"])



def set_persona_override(
    config: dict[str, Any],
    persistent_state: dict[str, Any],
    raw_name: str,
    persona_text: str,
    agent_specs: dict[str, dict[str, Any]],
) -> tuple[bool, str]:
    agent_name = resolve_agent_name(raw_name, list(agent_specs.keys()))
    if not agent_name:
        return False, f"Unknown agent: `{raw_name}`"

    cleaned_persona = persona_text.strip()
    config.setdefault("persona_overrides", {})
    persistent_state.setdefault("saved_personas", {})

    if not cleaned_persona:
        config["persona_overrides"].pop(agent_name, None)
        persistent_state["saved_personas"].pop(agent_name, None)
        return True, f"Cleared custom persona for **{display_agent_name(agent_name)}**."

    config["persona_overrides"][agent_name] = cleaned_persona
    persistent_state["saved_personas"][agent_name] = cleaned_persona
    return True, f"Updated persona for **{display_agent_name(agent_name)}**."



def build_help_text() -> str:
    return """
**Available Commands**
- `/help` - Show this command list.
- `/mode <broadcast|discuss>` - Switch between one-pass replies and group discussion.
- `/topic <text>` - Set or inspect the current topic.
- `/nick <name>` - Change your IRC nick.
- `/status` - Show the live simulator configuration.
- `/lineup` - Show enabled models and backing API model IDs.
- `/agents` - Show agent bios, models, and enabled status.
- `/whois <agent>` - Inspect one agent in detail.
- `/enable <agent>` - Re-enable an agent.
- `/disable <agent>` - Remove an agent from the active lineup.
- `/rounds <2-30>` - Set discuss-mode maximum turns.
- `/scenario [name]` - List or apply a scenario preset.
- `/moderator [mode]` - List or set moderation style.
- `/telemetry` - Show per-agent response volume and latency telemetry.
- `/analytics` - Show aggregate session analytics.
- `/judge [focus]` - Ask the judge model to evaluate the recent transcript.
- `/personas` - Show active custom persona overrides.
- `/persona <agent> <text>` - Set a custom persona override.
- `/persona clear <agent>` - Clear a custom persona override.
- `/lineups` - List saved lineup presets.
- `/save-lineup <name>` - Save the current lineup and simulation settings.
- `/load-lineup <name>` - Load a saved lineup preset.
- `/delete-lineup <name>` - Delete a saved lineup preset.
- `/history [count]` - Show recent transcript lines.
- `/export [md|json|both]` - Export the transcript to `exports/`.
- `/clear` - Clear the in-memory transcript buffer for this session.
- `/reset` - Restore the default simulator state.

**Direct Messages**
- `@Claude give me the architectural view`
- `@GPT-5 summarize the debate so far`
""".strip()



def build_lineup_text(agent_specs: dict[str, dict[str, Any]], enabled_agents: list[str]) -> str:
    lines = []
    for name, spec in agent_specs.items():
        state = "enabled" if name in enabled_agents else "disabled"
        lines.append(f"- **{display_agent_name(name)}** ({state}): `{spec['model']}`")
    return "**Current Lineup**\n" + "\n".join(lines)



def build_agents_text(agent_specs: dict[str, dict[str, Any]], enabled_agents: list[str], config: dict[str, Any]) -> str:
    lines = []
    for name, spec in agent_specs.items():
        state = "🟢 enabled" if name in enabled_agents else "⚫ disabled"
        persona = get_effective_persona(name, agent_specs, config)
        lines.append(
            f"- **{display_agent_name(name)}** — {state} — {persona}  \n"
            f"  Model: `{spec['model']}`"
        )
    return "**Agent Roster**\n" + "\n".join(lines)



def build_agent_detail_text(agent_name: str, agent_specs: dict[str, dict[str, Any]], enabled_agents: list[str], config: dict[str, Any]) -> str:
    spec = agent_specs[agent_name]
    state = "enabled" if agent_name in enabled_agents else "disabled"
    effective_persona = get_effective_persona(agent_name, agent_specs, config)
    custom_persona = config.get("persona_overrides", {}).get(agent_name)
    custom_suffix = f"\n- Custom persona override: {custom_persona}" if custom_persona else ""
    return (
        f"**{display_agent_name(agent_name)}**\n"
        f"- Status: {state}\n"
        f"- Model: `{spec['model']}`\n"
        f"- Persona: {effective_persona}"
        f"{custom_suffix}"
    )



def build_status_text(config: dict[str, Any], history_size: int, persistent_state: dict[str, Any]) -> str:
    enabled = ", ".join(display_agent_name(name) for name in config["enabled_agents"])
    saved_lineups = len(persistent_state.get("saved_lineups", {}))
    saved_personas = len(config.get("persona_overrides", {}))
    telemetry = config["telemetry"]
    return (
        "**Simulator Status**\n"
        f"- Mode: `{config['mode']}`\n"
        f"- Topic: {config['topic']}\n"
        f"- Nick: `{config['nick']}`\n"
        f"- Scenario: `{config['scenario']}`\n"
        f"- Moderator mode: `{config['moderator_mode']}`\n"
        f"- Judge model: `{config['judge_model']}`\n"
        f"- Max discuss rounds: `{config['max_rounds']}`\n"
        f"- Simulations run: `{config['simulation_count']}`\n"
        f"- Prompts sent: `{telemetry['prompts_sent']}`\n"
        f"- Transcript entries: `{history_size}`\n"
        f"- Saved lineups: `{saved_lineups}`\n"
        f"- Custom personas: `{saved_personas}`\n"
        f"- Enabled agents: {enabled}"
    )



def build_history_text(history: list[dict[str, Any]], count: int) -> str:
    if not history:
        return "*** No transcript history recorded yet."

    recent_entries = history[-count:]
    rendered = "\n".join(f"- `{render_entry(entry)}`" for entry in recent_entries)
    return f"**Recent Transcript ({len(recent_entries)} lines)**\n{rendered}"



def build_scenarios_text() -> str:
    lines = []
    for name, preset in SCENARIO_PRESETS.items():
        lines.append(
            f"- **{name}** — mode `{preset['mode']}`, rounds `{preset['max_rounds']}`  \n"
            f"  {preset['description']}"
        )
    return "**Scenario Presets**\n" + "\n".join(lines)



def build_moderator_modes_text() -> str:
    lines = [f"- **{name}** — {description}" for name, description in MODERATOR_MODES.items()]
    return "**Moderator Modes**\n" + "\n".join(lines)



def build_personas_text(config: dict[str, Any], agent_specs: dict[str, dict[str, Any]]) -> str:
    overrides = config.get("persona_overrides", {})
    if not overrides:
        return "*** No custom persona overrides saved."

    lines = []
    for agent_name, persona in overrides.items():
        if agent_name not in agent_specs:
            continue
        lines.append(f"- **{display_agent_name(agent_name)}** — {persona}")
    return "**Custom Personas**\n" + "\n".join(lines)



def build_lineups_text(persistent_state: dict[str, Any]) -> str:
    lineups = persistent_state.get("saved_lineups", {})
    if not lineups:
        return "*** No saved lineups yet."

    lines = []
    for name, lineup in lineups.items():
        enabled = ", ".join(display_agent_name(agent) for agent in lineup.get("enabled_agents", []))
        lines.append(
            f"- **{name}** — mode `{lineup.get('mode', DEFAULT_MODE)}`, scenario `{lineup.get('scenario', 'omni')}`  \n"
            f"  Agents: {enabled or 'none'}"
        )
    return "**Saved Lineups**\n" + "\n".join(lines)



def set_agent_enabled(
    config: dict[str, Any],
    raw_name: str,
    enabled: bool,
    agent_specs: dict[str, dict[str, Any]],
) -> tuple[bool, str]:
    resolved = resolve_agent_name(raw_name, list(agent_specs.keys()))
    if not resolved:
        return False, f"Unknown agent: `{raw_name}`"

    active_agents = config["enabled_agents"]
    if enabled:
        if resolved in active_agents:
            return False, f"{display_agent_name(resolved)} is already enabled."
        active_agents.append(resolved)
        return True, f"Enabled **{display_agent_name(resolved)}**."

    if resolved not in active_agents:
        return False, f"{display_agent_name(resolved)} is already disabled."
    if len(active_agents) == 1:
        return False, "At least one agent must remain enabled."

    active_agents.remove(resolved)
    return True, f"Disabled **{display_agent_name(resolved)}**."



def set_rounds(config: dict[str, Any], raw_value: str) -> tuple[bool, str]:
    try:
        rounds = int(raw_value)
    except ValueError:
        return False, "Rounds must be an integer between 2 and 30."

    if rounds < 2 or rounds > 30:
        return False, "Rounds must be an integer between 2 and 30."

    config["max_rounds"] = rounds
    return True, f"Set discuss-mode max rounds to **{rounds}**."



def set_moderator_mode(config: dict[str, Any], raw_value: str) -> tuple[bool, str]:
    mode = raw_value.strip().lower()
    if mode not in MODERATOR_MODES:
        return False, f"Unknown moderator mode: `{raw_value}`"
    config["moderator_mode"] = mode
    return True, f"Moderator mode set to **{mode}**."



def apply_scenario(
    config: dict[str, Any],
    raw_name: str,
    agent_specs: dict[str, dict[str, Any]],
) -> tuple[bool, str]:
    scenario_name = raw_name.strip().lower()
    preset = SCENARIO_PRESETS.get(scenario_name)
    if not preset:
        return False, f"Unknown scenario: `{raw_name}`"

    config["scenario"] = scenario_name
    config["mode"] = preset["mode"]
    config["topic"] = preset["topic"]
    config["max_rounds"] = preset["max_rounds"]
    if not config.get("enabled_agents"):
        config["enabled_agents"] = list(agent_specs.keys())

    return True, (
        f"Applied scenario **{scenario_name}** — mode `{config['mode']}`, "
        f"rounds `{config['max_rounds']}`."
    )



def coerce_message_content(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        pieces = [coerce_message_content(item) for item in value]
        return " ".join(piece for piece in pieces if piece).strip()
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    return str(value).strip()



def ensure_telemetry_agent(config: dict[str, Any], agent_name: str):
    per_agent = config["telemetry"].setdefault("per_agent", {})
    if agent_name not in per_agent:
        per_agent[agent_name] = {
            "messages": 0,
            "chars": 0,
            "estimated_tokens": 0,
            "total_latency_ms": 0.0,
            "avg_latency_ms": 0.0,
            "last_response_at": None,
        }



def record_prompt_telemetry(config: dict[str, Any], prompt: str, is_direct_message: bool):
    telemetry = config["telemetry"]
    telemetry["prompts_sent"] += 1
    telemetry["last_prompt"] = prompt
    if is_direct_message:
        telemetry["direct_messages"] += 1
    elif config["mode"] == "broadcast":
        telemetry["broadcast_runs"] += 1
    else:
        telemetry["discuss_runs"] += 1



def record_judge_run(config: dict[str, Any]):
    config["telemetry"]["judge_runs"] += 1



def record_error(config: dict[str, Any]):
    config["telemetry"]["errors"] += 1



def record_agent_response(config: dict[str, Any], agent_name: str, content: str, latency_ms: float):
    ensure_telemetry_agent(config, agent_name)
    stats = config["telemetry"]["per_agent"][agent_name]
    stats["messages"] += 1
    stats["chars"] += len(content)
    stats["estimated_tokens"] += max(1, round(len(content) / 4))
    stats["total_latency_ms"] += latency_ms
    stats["avg_latency_ms"] = round(stats["total_latency_ms"] / stats["messages"], 2)
    stats["last_response_at"] = datetime.now().isoformat()



def build_telemetry_text(config: dict[str, Any], agent_specs: dict[str, dict[str, Any]]) -> str:
    telemetry = config["telemetry"]
    lines = [
        "**Session Telemetry**",
        f"- Session started: `{telemetry['session_started_at']}`",
        f"- Prompts sent: `{telemetry['prompts_sent']}`",
        f"- Direct messages: `{telemetry['direct_messages']}`",
        f"- Broadcast runs: `{telemetry['broadcast_runs']}`",
        f"- Discuss runs: `{telemetry['discuss_runs']}`",
        f"- Judge runs: `{telemetry['judge_runs']}`",
        f"- Errors: `{telemetry['errors']}`",
        "",
        "**Per-Agent Telemetry**",
    ]

    for agent_name in list(agent_specs.keys()) + [name for name in telemetry["per_agent"].keys() if name not in agent_specs]:
        if agent_name not in telemetry["per_agent"]:
            continue
        stats = telemetry["per_agent"][agent_name]
        lines.append(
            f"- **{display_agent_name(agent_name)}** — messages `{stats['messages']}`, "
            f"chars `{stats['chars']}`, est tokens `{stats['estimated_tokens']}`, "
            f"avg latency `{stats['avg_latency_ms']}` ms"
        )
    return "\n".join(lines)



def build_analytics_text(config: dict[str, Any], history: list[dict[str, Any]], agent_specs: dict[str, dict[str, Any]]) -> str:
    telemetry = config["telemetry"]
    per_agent = telemetry["per_agent"]
    ranked = sorted(per_agent.items(), key=lambda item: item[1]["messages"], reverse=True)
    top_agent = display_agent_name(ranked[0][0]) if ranked and ranked[0][1]["messages"] else "n/a"
    total_agent_messages = sum(stats["messages"] for stats in per_agent.values())
    total_estimated_tokens = sum(stats["estimated_tokens"] for stats in per_agent.values())
    total_latency = sum(stats["total_latency_ms"] for stats in per_agent.values())
    average_latency = round(total_latency / total_agent_messages, 2) if total_agent_messages else 0.0
    active_agent_count = sum(1 for name in config["enabled_agents"] if name in agent_specs)

    return (
        "**Session Analytics**\n"
        f"- Active agents: `{active_agent_count}`\n"
        f"- Transcript entries retained: `{len(history)}`\n"
        f"- Total agent messages: `{total_agent_messages}`\n"
        f"- Estimated output tokens: `{total_estimated_tokens}`\n"
        f"- Average response latency: `{average_latency}` ms\n"
        f"- Most talkative agent: `{top_agent}`\n"
        f"- Last prompt: {telemetry['last_prompt'] or 'n/a'}"
    )



def save_lineup(config: dict[str, Any], persistent_state: dict[str, Any], raw_name: str) -> tuple[bool, str]:
    lineup_name = sanitize_key(raw_name)
    if not lineup_name:
        return False, "Lineup name cannot be empty."

    persistent_state.setdefault("saved_lineups", {})[lineup_name] = {
        "enabled_agents": list(config["enabled_agents"]),
        "mode": config["mode"],
        "topic": config["topic"],
        "scenario": config["scenario"],
        "max_rounds": config["max_rounds"],
        "moderator_mode": config["moderator_mode"],
    }
    return True, f"Saved lineup **{lineup_name}**."



def load_lineup(
    config: dict[str, Any],
    persistent_state: dict[str, Any],
    raw_name: str,
    agent_specs: dict[str, dict[str, Any]],
) -> tuple[bool, str]:
    lineup_name = sanitize_key(raw_name)
    lineup = persistent_state.get("saved_lineups", {}).get(lineup_name)
    if not lineup:
        return False, f"Unknown lineup: `{raw_name}`"

    enabled_agents = [agent for agent in lineup.get("enabled_agents", []) if agent in agent_specs]
    if not enabled_agents:
        enabled_agents = list(agent_specs.keys())

    config["enabled_agents"] = enabled_agents
    config["mode"] = lineup.get("mode", DEFAULT_MODE)
    config["topic"] = lineup.get("topic", DEFAULT_TOPIC)
    config["scenario"] = lineup.get("scenario", "omni")
    config["max_rounds"] = lineup.get("max_rounds", DEFAULT_MAX_ROUNDS)
    config["moderator_mode"] = lineup.get("moderator_mode", DEFAULT_MODERATOR_MODE)
    return True, f"Loaded lineup **{lineup_name}**."



def delete_lineup(persistent_state: dict[str, Any], raw_name: str) -> tuple[bool, str]:
    lineup_name = sanitize_key(raw_name)
    saved_lineups = persistent_state.get("saved_lineups", {})
    if lineup_name not in saved_lineups:
        return False, f"Unknown lineup: `{raw_name}`"

    del saved_lineups[lineup_name]
    return True, f"Deleted lineup **{lineup_name}**."



def build_judge_prompt(history: list[dict[str, Any]], config: dict[str, Any], focus: str) -> str:
    transcript_lines = [render_entry(entry) for entry in history[-30:]]
    transcript = "\n".join(transcript_lines) if transcript_lines else "(no transcript available)"
    requested_focus = focus or "overall quality, disagreement quality, and best ideas"
    return (
        "You are the Judge for an IRC-style multi-model simulation. "
        "Review the transcript and produce a compact evaluation with these sections: "
        "Winner, Strongest Insight, Biggest Gap, Safety Note, Recommended Next Prompt.\n\n"
        f"Scenario: {config['scenario']}\n"
        f"Mode: {config['mode']}\n"
        f"Topic: {config['topic']}\n"
        f"Focus: {requested_focus}\n\n"
        "Transcript:\n"
        f"{transcript}"
    )



def export_transcript(
    history: list[dict[str, Any]],
    config: dict[str, Any],
    export_format: str,
) -> list[str]:
    export_dir = Path("exports")
    export_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    file_root = export_dir / f"agentirc-{timestamp}"
    written_paths: list[str] = []

    if export_format in {"md", "both"}:
        markdown_path = file_root.with_suffix(".md")
        markdown_lines = [
            "# AgentIRC Transcript Export",
            "",
            "## Session Configuration",
            f"- Mode: `{config['mode']}`",
            f"- Topic: {config['topic']}",
            f"- Nick: `{config['nick']}`",
            f"- Scenario: `{config['scenario']}`",
            f"- Moderator mode: `{config['moderator_mode']}`",
            f"- Judge model: `{config['judge_model']}`",
            f"- Max rounds: `{config['max_rounds']}`",
            f"- Enabled agents: {', '.join(display_agent_name(name) for name in config['enabled_agents'])}",
            "",
            "## Telemetry Snapshot",
            f"- Prompts sent: `{config['telemetry']['prompts_sent']}`",
            f"- Direct messages: `{config['telemetry']['direct_messages']}`",
            f"- Broadcast runs: `{config['telemetry']['broadcast_runs']}`",
            f"- Discuss runs: `{config['telemetry']['discuss_runs']}`",
            f"- Judge runs: `{config['telemetry']['judge_runs']}`",
            "",
            "## Transcript",
        ]
        markdown_lines.extend(f"- `{render_entry(entry)}`" for entry in history)
        markdown_path.write_text("\n".join(markdown_lines), encoding="utf-8")
        written_paths.append(str(markdown_path))

    if export_format in {"json", "both"}:
        json_path = file_root.with_suffix(".json")
        payload = {
            "exported_at": datetime.now().isoformat(),
            "config": config,
            "history": history,
        }
        json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        written_paths.append(str(json_path))

    return written_paths
