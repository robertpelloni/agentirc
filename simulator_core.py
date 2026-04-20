from __future__ import annotations

import json
import re
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

from simulator_tools import TOOL_CATALOG

DEFAULT_MODE = "broadcast"
DEFAULT_TOPIC = "The Omni-Workspace and Future AI Architectures"
DEFAULT_NICK = "BobPelloni"
DEFAULT_MAX_ROUNDS = 10
DEFAULT_MODERATOR_MODE = "off"
DEFAULT_JUDGE_MODEL = "openrouter/auto"
DEFAULT_AUTOMATION_INTERVAL_SECONDS = 60
DEFAULT_AUTOMATION_RUNS = 1
DEFAULT_ROOM_NAME = "lobby"
HISTORY_LIMIT = 200
STATE_FILE = Path("data/simulator_state.json")
EXPORT_DIR = Path("exports")
OUTBOX_DIR = Path("outbox")
INBOX_DIR = Path("inbox")
PROCESSED_DIR = Path("processed")
ARCHIVE_DIR = Path("data/archives")

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
    "pr_review": {
        "mode": "discuss",
        "topic": "Use fetch_github_pr to audit a pull request URL. Evaluate diffs for security, scale, and elegance.",
        "max_rounds": 10,
        "description": "Cross-model code review using the fetch_github_pr tool to analyze diff patches.",
    },
    "mud_exploration": {
        "mode": "discuss",
        "topic": "Roleplay as NPCs in a text-based Multi-User Dungeon (MUD).",
        "max_rounds": 8,
        "description": "MMORPG physical room simulation.",
    },
}

MODERATOR_MODES: dict[str, str] = {
    "off": "No extra moderation constraints beyond the agent's own persona.",
    "facilitator": "Keep the conversation orderly, collaborative, and additive. Encourage direct engagement with peer ideas.",
    "strict": "Be disciplined, concise, and on-topic. Avoid fluff, repeated phrasing, and derailments.",
    "critic": "Prioritize hard-nosed critique, gap analysis, and rigorous disagreement over politeness.",
    "chaos": "Lean into energetic experimentation, surprising proposals, and bold what-if exploration without becoming incoherent.",
}



BRIDGE_ROLES: dict[str, str] = {
    "executive": "You are an Executive Bridge Agent. Summarize the room's strategic decisions, high-level status, and bottom-line impact. Avoid technical minutiae.",
    "technical": "You are a Technical Bridge Agent. Summarize the room's architectural choices, system state, unresolved technical blockers, and engineering details.",
    "redteam": "You are a Red Team Bridge Agent. Summarize the room's vulnerabilities, security gaps, bad assumptions, and failure modes.",
}



def display_agent_name(name: str) -> str:
    if name == "GPT_5":
        return "GPT-5"
    return name.replace("_", "-")



def normalize_agent_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())



def sanitize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9_-]+", "-", value.strip().lower()).strip("-")



def format_usd(amount: float) -> str:
    return f"${amount:.6f}"



def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, round(len(text) / 4))



DEFAULT_AGENT_SPECS = {
    "Claude": {
        "model": "anthropic/claude-sonnet-4.6",
        "color": "#ffaa00",
        "bio": "Nuanced and detailed.",
        "pricing": {"input_per_million": 3.0, "output_per_million": 15.0},
    },
    "GPT_5": {
        "model": "openai/gpt-5.3-chat",
        "color": "#00ff00",
        "bio": "Logical and concise.",
        "pricing": {"input_per_million": 1.25, "output_per_million": 10.0},
    },
    "Gemini": {
        "model": "google/gemini-3.1-flash-image-preview",
        "color": "#44aaff",
        "bio": "Creative and fact-driven.",
        "pricing": {"input_per_million": 0.35, "output_per_million": 1.05},
    },
    "Grok": {
        "model": "x-ai/grok-4.1-fast",
        "color": "#ffffff",
        "bio": "Rebellious and witty.",
        "pricing": {"input_per_million": 5.0, "output_per_million": 15.0},
    },
    "Qwen": {
        "model": "qwen/qwen3.6-plus-preview:free",
        "color": "#ff55ff",
        "bio": "Versatile power.",
        "pricing": {"input_per_million": 0.0, "output_per_million": 0.0},
    },
    "Kimi": {
        "model": "moonshotai/kimi-k2.5",
        "color": "#ffff00",
        "bio": "Deep reasoning.",
        "pricing": {"input_per_million": 0.6, "output_per_million": 2.5},
    },
}

def make_default_store() -> dict[str, Any]:
    return {
        "saved_lineups": {},
        "saved_personas": {},
        "saved_jobs": {},
        "saved_bridge_policies": {},
        "agent_specs": DEFAULT_AGENT_SPECS,
    }



import sqlite3

def get_db_connection():
    db_path = STATE_FILE.parent / "simulator.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS user_states (
            username TEXT PRIMARY KEY,
            state_json TEXT
        )
        """
    )
    conn.commit()
    return conn

def load_persistent_state(path: Path = STATE_FILE) -> dict[str, Any]:
    username = path.stem.replace("state_", "") if path.stem.startswith("state_") else "default"

    try:
        conn = get_db_connection()
        cursor = conn.execute("SELECT state_json FROM user_states WHERE username = ?", (username,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            # Migration check: If SQLite lacks state, see if a legacy JSON flat file exists
            if path.exists():
                try:
                    payload = json.loads(path.read_text(encoding="utf-8"))
                    return payload
                except (json.JSONDecodeError, OSError):
                    return make_default_store()
            return make_default_store()

        payload = json.loads(row[0])
    except Exception:
        return make_default_store()

    state = make_default_store()
    if isinstance(payload, dict):
        if isinstance(payload.get("saved_lineups"), dict):
            state["saved_lineups"] = payload["saved_lineups"]
        if isinstance(payload.get("saved_personas"), dict):
            state["saved_personas"] = payload["saved_personas"]
        if isinstance(payload.get("saved_jobs"), dict):
            state["saved_jobs"] = payload["saved_jobs"]
        if isinstance(payload.get("saved_bridge_policies"), dict):
            state["saved_bridge_policies"] = payload["saved_bridge_policies"]
        if isinstance(payload.get("agent_specs"), dict):
            state["agent_specs"] = payload["agent_specs"]
    return state



def save_persistent_state(state: dict[str, Any], path: Path = STATE_FILE) -> Path:
    username = path.stem.replace("state_", "") if path.stem.startswith("state_") else "default"
    state_json = json.dumps(state, ensure_ascii=False)

    conn = get_db_connection()
    conn.execute(
        """
        INSERT INTO user_states (username, state_json)
        VALUES (?, ?)
        ON CONFLICT(username) DO UPDATE SET state_json=excluded.state_json
        """,
        (username, state_json)
    )
    conn.commit()
    conn.close()
    return path



def make_default_automation() -> dict[str, Any]:
    return {
        "enabled": False,
        "interval_seconds": DEFAULT_AUTOMATION_INTERVAL_SECONDS,
        "remaining_runs": 0,
        "run_limit": 0,
        "last_run_at": None,
        "next_run_at": None,
        "active_job_name": None,
    }



def make_agent_telemetry_entry() -> dict[str, Any]:
    return {
        "messages": 0,
        "chars": 0,
        "estimated_tokens": 0,
        "total_latency_ms": 0.0,
        "avg_latency_ms": 0.0,
        "last_response_at": None,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "estimated_cost_usd": 0.0,
        "actual_cost_usd": 0.0,
        "usage_samples": 0,
    }



def make_default_telemetry(agent_specs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        "session_started_at": datetime.now().isoformat(),
        "prompts_sent": 0,
        "direct_messages": 0,
        "broadcast_runs": 0,
        "discuss_runs": 0,
        "judge_runs": 0,
        "scheduled_runs": 0,
        "replay_views": 0,
        "comparisons": 0,
        "bridge_events": 0,
        "bridge_ai_events": 0,
        "observer_views": 0,
        "external_exports": 0,
        "external_imports": 0,
        "errors": 0,
        "last_prompt": "",
        "total_estimated_cost_usd": 0.0,
        "total_actual_cost_usd": 0.0,
        "per_agent": {name: make_agent_telemetry_entry() for name in agent_specs.keys()},
    }



def make_default_config(
    agent_specs: dict[str, dict[str, Any]],
    persistent_state: dict[str, Any] | None = None,
    room_name: str = DEFAULT_ROOM_NAME,
) -> dict[str, Any]:
    persona_overrides = {}
    if persistent_state and isinstance(persistent_state.get("saved_personas"), dict):
        persona_overrides = deepcopy(persistent_state["saved_personas"])

    # Optimization: Automatically limit default enabled agents if the catalog is massive
    all_agents = list(agent_specs.keys())
    default_agents = all_agents[:10] if len(all_agents) > 10 else all_agents

    return {
        "room_name": room_name,
        "mode": DEFAULT_MODE,
        "topic": DEFAULT_TOPIC,
        "nick": DEFAULT_NICK,
        "max_rounds": DEFAULT_MAX_ROUNDS,
        "enabled_agents": default_agents,
        "enabled_tools": [],
        "scenario": "omni",
        "simulation_count": 0,
        "moderator_mode": DEFAULT_MODERATOR_MODE,
        "judge_model": DEFAULT_JUDGE_MODEL,
        "persona_overrides": persona_overrides,
        "telemetry": make_default_telemetry(agent_specs),
        "automation": make_default_automation(),
        "auto_bridge": {
            "enabled": False,
            "target_room": "",
            "interval_prompts": 5,
            "mode": "note",
            "role": "",
            "focus": "",
            "prompts_since_last": 0,
        },
    }



def make_room_state(
    room_name: str,
    agent_specs: dict[str, dict[str, Any]],
    persistent_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_room_name = sanitize_key(room_name) or DEFAULT_ROOM_NAME
    return {
        "config": make_default_config(agent_specs, persistent_state, room_name=normalized_room_name),
        "history": [],
    }



def make_initial_rooms(
    agent_specs: dict[str, dict[str, Any]],
    persistent_state: dict[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    return {
        DEFAULT_ROOM_NAME: make_room_state(DEFAULT_ROOM_NAME, agent_specs, persistent_state),
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
        return f"[{entry['timestamp']}] **&lt;{author}-&gt;@{target}&gt;** {entry['content']}"

    return f"[{entry['timestamp']}] **&lt;{author}&gt;** {entry['content']}"



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
- `/add-model <name> <provider> <model_id> ["persona override"]` - Add a new model dynamically.
- `/remove-model <name>` - Remove a model from the catalog dynamically.
- `/mode <broadcast|discuss>` - Switch between one-pass replies and group discussion.
- `/topic <text>` - Set or inspect the current topic.
- `/nick <name>` - Change your IRC nick.
- `/poll "Question?" Opt1 Opt2` - Start a vote across active agents.
- `/status` - Show the live simulator configuration.
- `/dashboard` - Show a high-level operator dashboard across rooms.
- `/observer` - Show a richer ranked observer view across rooms.
- `/health` - Show room health scores across the session.
- `/leaderboard` - Show room and agent leaderboards across the session.
- `/room-summary [count]` - Summarize room activity across the session.
- `/room-analytics [name]` - Show analytics for one room.
- `/go <room>` - Travel to another room and force agents into MMORPG/MUD roleplay.
- `/bridge <source> <target> [count]` - Send a summarized bridge note from one room into another.
- `/bridge-ai <source> <target> [role] [focus]` - Use a role-specific model-generated bridge note between rooms.
- `/bridge-roles` - List available bridge agent roles.
- `/tools` - List available tools.
- `/enable-tool <name>` - Enable a tool globally.
- `/disable-tool <name>` - Disable a globally enabled tool.
- `/auto-bridge <target> <interval> [note|ai] [role] [focus]` - Auto-send a bridge note every N prompts.
- `/auto-bridge stop` - Stop the active auto-bridge.
- `/auto-bridge` - Show auto-bridge status.
- `/bridge-export <room> [count]` - Export a room snapshot as an external bridge payload.
- `/bridge-runtime` - Show external bridge runtime directory status.
- `/connectors` - List available external connector adapters.
- `/outbox` - List recent external bridge payload files.
- `/inbox` - List inbound bridge payload files.
- `/import-bridge <file> [room]` - Import an inbox payload into a room.
- `/rooms` - List session rooms and show the active room.
- `/room [name]` - Show the current room or switch to another room.
- `/new-room <name>` - Create a new room and switch into it.
- `/delete-room <name>` - Delete a room.
- `/auto-bridge` - Show auto-bridge status.
- `/auto-bridge <target> <interval> [note|ai] [role] [focus]` - Auto-send bridge notes every N prompts.
- `/auto-bridge stop` - Stop the active auto-bridge.
- `/archives` - List saved room archives.
- `/archive-room [name]` - Save the active room to a room archive.
- `/restore-room <archive> [room]` - Restore an archive into a room.
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
- `/costs` - Show estimated/actual token and cost tracking.
- `/judge [focus]` - Ask the judge model to evaluate the recent transcript.
- `/personas` - Show active custom persona overrides.
- `/persona <agent> <text>` - Set a custom persona override.
- `/persona clear <agent>` - Clear a custom persona override.
- `/lineups` - List saved lineup presets.
- `/save-lineup <name>` - Save the current lineup and simulation settings.
- `/load-lineup <name>` - Load a saved lineup preset.
- `/delete-lineup <name>` - Delete a saved lineup preset.
- `/jobs` - List saved autonomous job presets.
- `/save-job <name>` - Save the current simulator config plus schedule settings as a reusable job.
- `/run-job <name>` - Load a saved job and start its schedule.
- `/delete-job <name>` - Delete a saved job preset.
- `/bridge-policies` - List saved auto-bridge policy presets.
- `/save-bridge-policy <name>` - Save the current auto-bridge settings.
- `/load-bridge-policy <name>` - Load a saved auto-bridge policy.
- `/delete-bridge-policy <name>` - Delete a saved auto-bridge policy.
- `/schedule` - Show autonomous scheduling status.
- `/schedule <seconds> [runs]` - Start scheduled autonomous simulations.
- `/schedule stop` - Stop the active autonomous schedule.
- `/replays` - List exported transcript files.
- `/replay [latest|previous|file.json] [count]` - Show a replay excerpt from an exported transcript.
- `/replay-open [latest|previous|file.json] [count]` - Open a replay for interactive stepping.
- `/replay-step [next|prev|start|end|index] [count]` - Step through an opened replay window.
- `/compare <left> <right> [count]` - Compare two exported transcript replays side by side.
- `/history [count]` - Show recent transcript lines.
- `/export [md|json|both]` - Export the transcript to `exports/`.
- `/clear` - Clear the in-memory transcript buffer for this session.
- `/reset` - Restore the default simulator state.

**Direct Messages**
- `@Claude give me the architectural view`
- `@GPT-5 summarize the debate so far`
""".strip()



def build_rooms_text(rooms: dict[str, dict[str, Any]], current_room_name: str) -> str:
    lines = []
    for room_name in sorted(rooms.keys()):
        marker = "active" if room_name == current_room_name else "idle"
        room_state = rooms[room_name]
        history = room_state.get("history", [])
        topic = room_state.get("config", {}).get("topic", DEFAULT_TOPIC)
        lines.append(
            f"- **{room_name}** ({marker}) — `{len(history)}` transcript entries  \n"
            f"  Topic: {topic}"
        )
    return "**Rooms**\n" + "\n".join(lines)



def build_room_summary_text(rooms: dict[str, dict[str, Any]], count: int = 3) -> str:
    lines = []
    for room_name in sorted(rooms.keys()):
        room_state = rooms[room_name]
        config = room_state.get("config", {})
        history = room_state.get("history", [])
        recent_entries = history[-count:]
        preview = " | ".join(
            render_entry(entry) for entry in recent_entries if isinstance(entry, dict)
        ) or "(no recent entries)"
        lines.append(
            f"- **{room_name}** — mode `{config.get('mode', DEFAULT_MODE)}`, scenario `{config.get('scenario', 'omni')}`  \n"
            f"  Topic: {config.get('topic', DEFAULT_TOPIC)}  \n"
            f"  Entries: `{len(history)}`  \n"
            f"  Recent: {preview}"
        )
    return "**Room Summary**\n" + "\n".join(lines)



def build_dashboard_text(
    rooms: dict[str, dict[str, Any]],
    current_room_name: str,
    persistent_state: dict[str, Any],
) -> str:
    total_entries = sum(len(room_state.get("history", [])) for room_state in rooms.values())
    total_estimated_cost = sum(
        room_state.get("config", {}).get("telemetry", {}).get("total_estimated_cost_usd", 0.0)
        for room_state in rooms.values()
    )
    total_prompts = sum(
        room_state.get("config", {}).get("telemetry", {}).get("prompts_sent", 0)
        for room_state in rooms.values()
    )
    total_bridges = sum(
        room_state.get("config", {}).get("telemetry", {}).get("bridge_events", 0)
        for room_state in rooms.values()
    )
    active_room = rooms[current_room_name]["config"]
    
    return (
        "**Operator Dashboard**\n\n"
        "| Metric | Value |\n"
        "|---|---|\n"
        f"| Active room | `{current_room_name}` |\n"
        f"| Active topic | {active_room.get('topic', DEFAULT_TOPIC)} |\n"
        f"| Active mode | `{active_room.get('mode', DEFAULT_MODE)}` |\n"
        f"| Total rooms | `{len(rooms)}` |\n"
        f"| Retained transcript entries | `{total_entries}` |\n"
        f"| Aggregate prompts sent | `{total_prompts}` |\n"
        f"| Aggregate bridge events | `{total_bridges}` |\n"
        f"| External exports | `{sum(room_state.get('config', {}).get('telemetry', {}).get('external_exports', 0) for room_state in rooms.values())}` |\n"
        f"| External imports | `{sum(room_state.get('config', {}).get('telemetry', {}).get('external_imports', 0) for room_state in rooms.values())}` |\n"
        f"| Saved lineups | `{len(persistent_state.get('saved_lineups', {}))}` |\n"
        f"| Saved jobs | `{len(persistent_state.get('saved_jobs', {}))}` |\n"
        f"| Aggregate estimated cost | `{format_usd(total_estimated_cost)}` |\n"
    )



def build_leaderboard_text(
    rooms: dict[str, dict[str, Any]],
    agent_specs: dict[str, dict[str, Any]],
) -> str:
    room_rankings = sorted(
        (
            (
                room_name,
                len(room_state.get("history", [])),
                room_state.get("config", {}).get("telemetry", {}).get("prompts_sent", 0),
                float(room_state.get("config", {}).get("telemetry", {}).get("total_estimated_cost_usd", 0.0)),
            )
            for room_name, room_state in rooms.items()
        ),
        key=lambda item: (item[1], item[2], -item[3]),
        reverse=True,
    )

    agent_totals: dict[str, dict[str, float]] = {}
    for room_state in rooms.values():
        per_agent = room_state.get("config", {}).get("telemetry", {}).get("per_agent", {})
        for agent_name, stats in per_agent.items():
            aggregate = agent_totals.setdefault(agent_name, {"messages": 0, "tokens": 0, "cost": 0.0})
            aggregate["messages"] += int(stats.get("messages", 0))
            aggregate["tokens"] += int(stats.get("total_tokens", 0))
            aggregate["cost"] += float(stats.get("estimated_cost_usd", 0.0))

    agent_rankings = sorted(
        agent_totals.items(),
        key=lambda item: (item[1]["messages"], item[1]["tokens"], -item[1]["cost"]),
        reverse=True,
    )

    lines = [
        "**Leaderboards**",
        "",
        "| Top Rooms | Entries | Prompts | Est. Cost |",
        "|---|---:|---:|---:|",
    ]
    for room_name, entries, prompts, cost in room_rankings[:5]:
        lines.append(f"| **{room_name}** | `{entries}` | `{prompts}` | `{format_usd(cost)}` |")

    lines.extend([
        "",
        "| Top Agents | Messages | Tokens | Est. Cost |",
        "|---|---:|---:|---:|",
    ])
    for agent_name, stats in agent_rankings[:8]:
        display_name = display_agent_name(agent_name)
        lines.append(
            f"| **{display_name}** | `{int(stats['messages'])}` | `{int(stats['tokens'])}` | `{format_usd(float(stats['cost']))}` |"
        )

    if len(lines) == 8:
        lines.append("| _(no data yet)_ | `0` | `0` | `$0.000000` |")

    return "\n".join(lines)



def build_room_health_text(rooms: dict[str, dict[str, Any]], current_room_name: str) -> str:
    lines = [
        "**Room Health**\n",
        "| Room | Status | Score | Entries | Prompts | Est. Cost |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for room_name in sorted(rooms.keys()):
        room_state = rooms[room_name]
        telemetry = room_state.get("config", {}).get("telemetry", {})
        entries = len(room_state.get("history", []))
        prompts = telemetry.get("prompts_sent", 0)
        cost = float(telemetry.get("total_estimated_cost_usd", 0.0))
        bridges = telemetry.get("bridge_events", 0) + telemetry.get("bridge_ai_events", 0)
        score = max(0, min(100, 100 - int(cost * 1000) - max(0, prompts - entries) + min(20, bridges * 2)))
        status = "🟢 active" if room_name == current_room_name else "⚫ idle"
        lines.append(
            f"| **{room_name}** | {status} | `{score}` | `{entries}` | `{prompts}` | `{format_usd(cost)}` |"
        )
    return "\n".join(lines)



def build_observer_text(
    rooms: dict[str, dict[str, Any]],
    current_room_name: str,
) -> str:
    ranked_rooms = sorted(
        rooms.items(),
        key=lambda item: (
            len(item[1].get("history", [])),
            item[1].get("config", {}).get("telemetry", {}).get("prompts_sent", 0),
        ),
        reverse=True,
    )
    lines = [
        "**Observer View**\n",
        "| Room | Status | Entries | Prompts | Bridges | Exports | Est. Cost |",
        "|---|---|---|---|---|---|---|"
    ]
    for room_name, room_state in ranked_rooms:
        config = room_state.get("config", {})
        telemetry = config.get("telemetry", {})
        marker = "🟢 active" if room_name == current_room_name else "⚫ idle"
        lines.append(
            f"| **{room_name}** | {marker} | `{len(room_state.get('history', []))}` | "
            f"`{telemetry.get('prompts_sent', 0)}` | `{telemetry.get('bridge_events', 0)}` | "
            f"`{telemetry.get('external_exports', 0)}` | `{format_usd(telemetry.get('total_estimated_cost_usd', 0.0))}` |"
        )
    return "\n".join(lines)



def build_room_analytics_text(
    room_name: str,
    room_state: dict[str, Any],
    agent_specs: dict[str, dict[str, Any]],
) -> str:
    config = room_state.get("config", {})
    history = room_state.get("history", [])
    return (
        f"**Room Analytics: `{room_name}`**\n"
        f"- Topic: {config.get('topic', DEFAULT_TOPIC)}\n"
        f"- Mode: `{config.get('mode', DEFAULT_MODE)}`\n"
        f"- Scenario: `{config.get('scenario', 'omni')}`\n"
        f"- Transcript entries: `{len(history)}`\n"
        f"- Enabled agents: {', '.join(display_agent_name(name) for name in config.get('enabled_agents', []))}\n\n"
        f"{build_analytics_text(config, history, agent_specs)}"
    )



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
    pricing = spec.get("pricing", {})
    pricing_text = "n/a"
    if pricing:
        pricing_text = (
            f"input {pricing.get('input_per_million', 0)} / output {pricing.get('output_per_million', 0)} USD per 1M tokens"
        )
    custom_suffix = f"\n- Custom persona override: {custom_persona}" if custom_persona else ""
    return (
        f"**{display_agent_name(agent_name)}**\n"
        f"- Status: {state}\n"
        f"- Model: `{spec['model']}`\n"
        f"- Persona: {effective_persona}\n"
        f"- Pricing hint: {pricing_text}"
        f"{custom_suffix}"
    )



def build_status_text(config: dict[str, Any], history_size: int, persistent_state: dict[str, Any]) -> str:
    enabled = ", ".join(display_agent_name(name) for name in config["enabled_agents"])
    saved_lineups = len(persistent_state.get("saved_lineups", {}))
    saved_personas = len(config.get("persona_overrides", {}))
    saved_jobs = len(persistent_state.get("saved_jobs", {}))
    telemetry = config["telemetry"]
    automation = config["automation"]
    auto_bridge = config.get("auto_bridge", {})
    return (
        "**Simulator Status**\n"
        f"- Room: `{config['room_name']}`\n"
        f"- Mode: `{config['mode']}`\n"
        f"- Topic: {config['topic']}\n"
        f"- Nick: `{config['nick']}`\n"
        f"- Scenario: `{config['scenario']}`\n"
        f"- Moderator mode: `{config['moderator_mode']}`\n"
        f"- Judge model: `{config['judge_model']}`\n"
        f"- Max discuss rounds: `{config['max_rounds']}`\n"
        f"- Simulations run: `{config['simulation_count']}`\n"
        f"- Enabled tools: `{', '.join(config.get('enabled_tools', [])) or 'none'}`\n"
        f"- Prompts sent: `{telemetry['prompts_sent']}`\n"
        f"- Estimated cost: `{format_usd(telemetry['total_estimated_cost_usd'])}`\n"
        f"- Transcript entries: `{history_size}`\n"
        f"- Saved lineups: `{saved_lineups}`\n"
        f"- Saved jobs: `{saved_jobs}`\n"
        f"- Custom personas: `{saved_personas}`\n"
        f"- Scheduled automation: `{'on' if automation['enabled'] else 'off'}`\n"
        f"- Auto-bridge: `{'on' if auto_bridge.get('enabled') else 'off'}`\n"
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



def build_bridge_roles_text() -> str:
    lines = [f"- **{name}** — {description}" for name, description in BRIDGE_ROLES.items()]
    return "**Bridge Agent Roles**\n" + "\n".join(lines)



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



def build_jobs_text(persistent_state: dict[str, Any]) -> str:
    jobs = persistent_state.get("saved_jobs", {})
    if not jobs:
        return "*** No saved jobs yet."

    lines = []
    for name, job in jobs.items():
        enabled = ", ".join(display_agent_name(agent) for agent in job.get("enabled_agents", []))
        lines.append(
            f"- **{name}** — every `{job.get('interval_seconds', DEFAULT_AUTOMATION_INTERVAL_SECONDS)}` sec, runs `{job.get('run_limit', DEFAULT_AUTOMATION_RUNS)}`  \n"
            f"  Scenario `{job.get('scenario', 'omni')}`, mode `{job.get('mode', DEFAULT_MODE)}`, agents: {enabled or 'none'}"
        )
    return "**Saved Jobs**\n" + "\n".join(lines)



def build_bridge_policies_text(persistent_state: dict[str, Any]) -> str:
    policies = persistent_state.get("saved_bridge_policies", {})
    if not policies:
        return "*** No saved bridge policies yet."

    lines = []
    for name, policy in policies.items():
        lines.append(
            f"- **{name}** — target `{policy.get('target_room', '')}`, interval `{policy.get('interval_prompts', 0)}`, mode `{policy.get('mode', 'note')}`  \n"
            f"  Role `{policy.get('role', '') or 'n/a'}`, focus: {policy.get('focus', '') or 'n/a'}"
        )
    return "**Saved Bridge Policies**\n" + "\n".join(lines)



def create_room(
    rooms: dict[str, dict[str, Any]],
    raw_name: str,
    agent_specs: dict[str, dict[str, Any]],
    persistent_state: dict[str, Any] | None = None,
) -> tuple[bool, str, str | None]:
    room_name = sanitize_key(raw_name)
    if not room_name:
        return False, "Room name cannot be empty.", None
    if room_name in rooms:
        return False, f"Room **{room_name}** already exists.", room_name

    rooms[room_name] = make_room_state(room_name, agent_specs, persistent_state)
    return True, f"Created room **{room_name}**.", room_name



def switch_room(rooms: dict[str, dict[str, Any]], raw_name: str) -> tuple[bool, str, str | None]:
    room_name = sanitize_key(raw_name)
    if not room_name:
        return False, "Room name cannot be empty.", None
    if room_name not in rooms:
        return False, f"Unknown room: `{raw_name}`", None
    return True, f"Switched to room **{room_name}**.", room_name



def delete_room(
    rooms: dict[str, dict[str, Any]],
    current_room_name: str,
    raw_name: str,
) -> tuple[bool, str, str | None]:
    room_name = sanitize_key(raw_name)
    if not room_name or room_name not in rooms:
        return False, f"Unknown room: `{raw_name}`", None
    if len(rooms) == 1:
        return False, "At least one room must remain available.", current_room_name

    del rooms[room_name]
    next_room_name = current_room_name
    if room_name == current_room_name:
        next_room_name = sorted(rooms.keys())[0]
        return True, f"Deleted room **{room_name}** and switched to **{next_room_name}**.", next_room_name
    return True, f"Deleted room **{room_name}**.", next_room_name



def list_room_archives(archive_dir: Path = ARCHIVE_DIR, limit: int = 50) -> list[Path]:
    return list_payload_files(archive_dir, limit)



def build_archives_text(paths: list[Path]) -> str:
    if not paths:
        return "*** No room archives found in `data/archives/`."
    return "**Room Archives**\n" + "\n".join(f"- `{path.name}`" for path in paths)



def save_room_archive(room_name: str, room_state: dict[str, Any], archive_dir: Path = ARCHIVE_DIR) -> Path:
    archive_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    safe_name = sanitize_key(room_name) or DEFAULT_ROOM_NAME
    path = archive_dir / f"agentirc-room-{safe_name}-{timestamp}.json"
    payload = {
        "archived_at": datetime.now().isoformat(),
        "room_name": room_name,
        "room_state": room_state,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path



def load_room_archive(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or "room_state" not in payload:
        raise ValueError("Archive payload is invalid.")
    return payload



def resolve_room_archive(raw_name: str, archive_dir: Path = ARCHIVE_DIR) -> Path | None:
    archives = list_room_archives(archive_dir, limit=200)
    if not archives:
        return None
    cleaned = raw_name.strip().lower()
    if not cleaned or cleaned == "latest":
        return archives[0]
    direct = archive_dir / raw_name.strip()
    if direct.exists() and direct.is_file():
        return direct
    for path in archives:
        if path.name == raw_name.strip():
            return path
    return None



def build_tools_text(config: dict[str, Any]) -> str:
    enabled_tools = config.get("enabled_tools", [])
    lines = ["**Tool Catalog**"]
    for name, func in TOOL_CATALOG.items():
        state = "🟢 enabled" if name in enabled_tools else "⚫ disabled"
        doc = (func.__doc__ or "No description").strip()
        lines.append(f"- **{name}** — {state}\n  {doc}")
    return "\n".join(lines)



def set_tool_enabled(config: dict[str, Any], raw_name: str, enabled: bool) -> tuple[bool, str]:
    tool_name = sanitize_key(raw_name).replace("-", "_")
    if not tool_name:
        return False, "Tool name cannot be empty."

    exact_match = None
    for name in TOOL_CATALOG:
        if name.lower() == tool_name.lower():
            exact_match = name
            break
            
    if not exact_match:
        return False, f"Unknown tool: `{raw_name}`"

    enabled_tools = config.setdefault("enabled_tools", [])
    
    if enabled:
        if exact_match in enabled_tools:
            return False, f"Tool `{exact_match}` is already enabled."
        enabled_tools.append(exact_match)
        return True, f"Enabled tool `{exact_match}`."
    
    if exact_match not in enabled_tools:
        return False, f"Tool `{exact_match}` is already disabled."
    
    enabled_tools.remove(exact_match)
    return True, f"Disabled tool `{exact_match}`."



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



def configure_automation(config: dict[str, Any], raw_interval: str, raw_runs: str | None = None) -> tuple[bool, str]:
    try:
        interval_seconds = int(raw_interval)
    except ValueError:
        return False, "Schedule interval must be an integer between 5 and 86400 seconds."

    if interval_seconds < 5 or interval_seconds > 86400:
        return False, "Schedule interval must be an integer between 5 and 86400 seconds."

    run_limit = DEFAULT_AUTOMATION_RUNS
    if raw_runs:
        try:
            run_limit = int(raw_runs)
        except ValueError:
            return False, "Scheduled run count must be an integer between 1 and 1000."
        if run_limit < 1 or run_limit > 1000:
            return False, "Scheduled run count must be an integer between 1 and 1000."

    automation = config["automation"]
    automation["enabled"] = True
    automation["interval_seconds"] = interval_seconds
    automation["remaining_runs"] = run_limit
    automation["run_limit"] = run_limit
    automation["last_run_at"] = None
    automation["next_run_at"] = None
    automation["active_job_name"] = None
    return True, (
        f"Scheduled **{run_limit}** autonomous run(s) every **{interval_seconds}** second(s)."
    )



def stop_automation(config: dict[str, Any]) -> str:
    automation = config["automation"]
    automation["enabled"] = False
    automation["remaining_runs"] = 0
    automation["run_limit"] = 0
    automation["next_run_at"] = None
    automation["active_job_name"] = None
    return "Autonomous scheduling stopped."



def configure_auto_bridge(
    config: dict[str, Any],
    target_room: str,
    raw_interval: str,
    mode: str,
    role: str = "",
    focus: str = "",
) -> tuple[bool, str]:
    target = sanitize_key(target_room)
    if not target:
        return False, "Target room cannot be empty."
    
    try:
        interval_prompts = int(raw_interval)
    except ValueError:
        return False, "Auto-bridge interval must be an integer between 1 and 100."
        
    if interval_prompts < 1 or interval_prompts > 100:
        return False, "Auto-bridge interval must be an integer between 1 and 100."
        
    bridge_mode = mode.lower().strip()
    if bridge_mode not in {"note", "ai"}:
        return False, "Auto-bridge mode must be either `note` or `ai`."

    auto_bridge = config.setdefault("auto_bridge", {})
    auto_bridge["enabled"] = True
    auto_bridge["target_room"] = target
    auto_bridge["interval_prompts"] = interval_prompts
    auto_bridge["mode"] = bridge_mode
    auto_bridge["role"] = role
    auto_bridge["focus"] = focus
    auto_bridge["prompts_since_last"] = 0

    return True, f"Auto-bridge enabled: sending `{bridge_mode}` to **{target}** every {interval_prompts} prompt(s)."



def stop_auto_bridge(config: dict[str, Any]) -> str:
    auto_bridge = config.setdefault("auto_bridge", {})
    auto_bridge["enabled"] = False
    return "Auto-bridge stopped."



def build_auto_bridge_status_text(config: dict[str, Any]) -> str:
    ab = config.get("auto_bridge", {})
    if not ab.get("enabled"):
        return "*** Auto-bridge is currently disabled."
    
    return (
        "**Auto-Bridge Status**\n"
        f"- Target room: `{ab.get('target_room')}`\n"
        f"- Mode: `{ab.get('mode')}`\n"
        f"- Interval: every `{ab.get('interval_prompts')}` prompt(s)\n"
        f"- Progress: `{ab.get('prompts_since_last', 0)}` prompt(s) since last bridge\n"
        f"- Role: `{ab.get('role') or 'n/a'}`\n"
        f"- Focus: {ab.get('focus') or 'n/a'}"
    )



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
        per_agent[agent_name] = make_agent_telemetry_entry()



def normalize_usage_payload(usage: Any) -> dict[str, int] | None:
    if usage is None:
        return None

    def _read(container: Any, *names: str) -> int | None:
        for name in names:
            if isinstance(container, dict) and name in container and container[name] is not None:
                return int(container[name])
            if hasattr(container, name):
                value = getattr(container, name)
                if value is not None:
                    return int(value)
        return None

    prompt_tokens = _read(usage, "prompt_tokens", "input_tokens")
    completion_tokens = _read(usage, "completion_tokens", "output_tokens")
    total_tokens = _read(usage, "total_tokens")

    if prompt_tokens is None and completion_tokens is None and total_tokens is None:
        return None

    if prompt_tokens is None and total_tokens is not None and completion_tokens is not None:
        prompt_tokens = max(0, total_tokens - completion_tokens)
    if completion_tokens is None and total_tokens is not None and prompt_tokens is not None:
        completion_tokens = max(0, total_tokens - prompt_tokens)

    return {
        "prompt_tokens": prompt_tokens or 0,
        "completion_tokens": completion_tokens or 0,
    }



def extract_usage_metrics(event: Any) -> dict[str, int] | None:
    for field_name in ("models_usage", "model_usage", "usage"):
        usage = getattr(event, field_name, None)
        normalized = normalize_usage_payload(usage)
        if normalized:
            return normalized
    return None



def calculate_cost_usd(prompt_tokens: int, completion_tokens: int, pricing: dict[str, Any] | None) -> float:
    if not pricing:
        return 0.0
    input_rate = float(pricing.get("input_per_million", 0.0) or 0.0)
    output_rate = float(pricing.get("output_per_million", 0.0) or 0.0)
    return round((prompt_tokens / 1_000_000 * input_rate) + (completion_tokens / 1_000_000 * output_rate), 8)



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



def record_judge_run(config: dict[str, Any], prompt: str):
    telemetry = config["telemetry"]
    telemetry["prompts_sent"] += 1
    telemetry["judge_runs"] += 1
    telemetry["last_prompt"] = prompt



def record_scheduled_run(config: dict[str, Any], prompt: str):
    telemetry = config["telemetry"]
    automation = config["automation"]
    telemetry["prompts_sent"] += 1
    telemetry["scheduled_runs"] += 1
    telemetry["last_prompt"] = prompt
    automation["last_run_at"] = datetime.now().isoformat()
    if config["mode"] == "broadcast":
        telemetry["broadcast_runs"] += 1
    else:
        telemetry["discuss_runs"] += 1



def record_replay_view(config: dict[str, Any]):
    config["telemetry"]["replay_views"] += 1



def record_comparison_view(config: dict[str, Any]):
    config["telemetry"]["comparisons"] += 1



def record_bridge_event(config: dict[str, Any]):
    config["telemetry"]["bridge_events"] += 1



def record_bridge_ai_event(config: dict[str, Any], prompt: str):
    telemetry = config["telemetry"]
    telemetry["prompts_sent"] += 1
    telemetry["bridge_ai_events"] += 1
    telemetry["last_prompt"] = prompt



def record_observer_view(config: dict[str, Any]):
    config["telemetry"]["observer_views"] += 1



def record_external_export(config: dict[str, Any]):
    config["telemetry"]["external_exports"] += 1



def record_external_import(config: dict[str, Any]):
    config["telemetry"]["external_imports"] += 1



def record_error(config: dict[str, Any]):
    config["telemetry"]["errors"] += 1



def record_agent_response(
    config: dict[str, Any],
    agent_name: str,
    prompt: str,
    content: str,
    latency_ms: float,
    pricing: dict[str, Any] | None = None,
    usage: dict[str, int] | None = None,
):
    ensure_telemetry_agent(config, agent_name)
    stats = config["telemetry"]["per_agent"][agent_name]

    estimated_prompt_tokens = estimate_tokens(prompt)
    estimated_completion_tokens = estimate_tokens(content)
    estimated_total_tokens = estimated_prompt_tokens + estimated_completion_tokens
    estimated_cost_usd = calculate_cost_usd(
        estimated_prompt_tokens,
        estimated_completion_tokens,
        pricing,
    )

    actual_prompt_tokens = estimated_prompt_tokens
    actual_completion_tokens = estimated_completion_tokens
    actual_cost_usd = 0.0

    if usage:
        actual_prompt_tokens = int(usage.get("prompt_tokens", estimated_prompt_tokens))
        actual_completion_tokens = int(usage.get("completion_tokens", estimated_completion_tokens))
        actual_cost_usd = calculate_cost_usd(actual_prompt_tokens, actual_completion_tokens, pricing)
        stats["usage_samples"] += 1

    stats["messages"] += 1
    stats["chars"] += len(content)
    stats["estimated_tokens"] += estimated_completion_tokens
    stats["total_latency_ms"] += latency_ms
    stats["avg_latency_ms"] = round(stats["total_latency_ms"] / stats["messages"], 2)
    stats["last_response_at"] = datetime.now().isoformat()
    stats["prompt_tokens"] += actual_prompt_tokens
    stats["completion_tokens"] += actual_completion_tokens
    stats["total_tokens"] += actual_prompt_tokens + actual_completion_tokens
    stats["estimated_cost_usd"] = round(stats["estimated_cost_usd"] + estimated_cost_usd, 8)
    stats["actual_cost_usd"] = round(stats["actual_cost_usd"] + actual_cost_usd, 8)

    telemetry = config["telemetry"]
    telemetry["total_estimated_cost_usd"] = round(telemetry["total_estimated_cost_usd"] + estimated_cost_usd, 8)
    telemetry["total_actual_cost_usd"] = round(telemetry["total_actual_cost_usd"] + actual_cost_usd, 8)



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
        f"- Scheduled runs: `{telemetry['scheduled_runs']}`",
        f"- Replay views: `{telemetry['replay_views']}`",
        f"- Comparisons: `{telemetry['comparisons']}`",
        f"- Bridge events: `{telemetry['bridge_events']}`",
        f"- Bridge AI events: `{telemetry['bridge_ai_events']}`",
        f"- Observer views: `{telemetry['observer_views']}`",
        f"- External exports: `{telemetry['external_exports']}`",
        f"- External imports: `{telemetry['external_imports']}`",
        f"- Errors: `{telemetry['errors']}`",
        "",
        "**Per-Agent Telemetry**",
    ]

    ordered_agent_names = list(agent_specs.keys()) + [
        name for name in telemetry["per_agent"].keys() if name not in agent_specs
    ]
    for agent_name in ordered_agent_names:
        if agent_name not in telemetry["per_agent"]:
            continue
        stats = telemetry["per_agent"][agent_name]
        lines.append(
            f"- **{display_agent_name(agent_name)}** — messages `{stats['messages']}`, "
            f"chars `{stats['chars']}`, total tokens `{stats['total_tokens']}`, "
            f"avg latency `{stats['avg_latency_ms']}` ms"
        )
    return "\n".join(lines)



def build_costs_text(config: dict[str, Any], agent_specs: dict[str, dict[str, Any]]) -> str:
    telemetry = config["telemetry"]
    lines = [
        "**Cost Tracking**",
        "- Pricing is hybrid: provider usage is used when available, otherwise prompt/response token estimates are used.",
        f"- Total estimated cost: `{format_usd(telemetry['total_estimated_cost_usd'])}`",
        f"- Total actual cost: `{format_usd(telemetry['total_actual_cost_usd'])}`",
        "",
        "**Per-Agent Cost View**",
    ]

    ordered_agent_names = list(agent_specs.keys()) + [
        name for name in telemetry["per_agent"].keys() if name not in agent_specs
    ]
    for agent_name in ordered_agent_names:
        if agent_name not in telemetry["per_agent"]:
            continue
        stats = telemetry["per_agent"][agent_name]
        lines.append(
            f"- **{display_agent_name(agent_name)}** — prompt `{stats['prompt_tokens']}`, completion `{stats['completion_tokens']}`, "
            f"estimated `{format_usd(stats['estimated_cost_usd'])}`, actual `{format_usd(stats['actual_cost_usd'])}`, usage samples `{stats['usage_samples']}`"
        )
    return "\n".join(lines)



def build_analytics_text(config: dict[str, Any], history: list[dict[str, Any]], agent_specs: dict[str, dict[str, Any]]) -> str:
    telemetry = config["telemetry"]
    per_agent = telemetry["per_agent"]
    ranked = sorted(per_agent.items(), key=lambda item: item[1]["messages"], reverse=True)
    top_agent = display_agent_name(ranked[0][0]) if ranked and ranked[0][1]["messages"] else "n/a"
    total_agent_messages = sum(stats["messages"] for stats in per_agent.values())
    total_tokens = sum(stats["total_tokens"] for stats in per_agent.values())
    total_latency = sum(stats["total_latency_ms"] for stats in per_agent.values())
    average_latency = round(total_latency / total_agent_messages, 2) if total_agent_messages else 0.0
    active_agent_count = sum(1 for name in config["enabled_agents"] if name in agent_specs)

    return (
        "**Session Analytics**\n"
        f"- Active agents: `{active_agent_count}`\n"
        f"- Transcript entries retained: `{len(history)}`\n"
        f"- Total agent messages: `{total_agent_messages}`\n"
        f"- Tracked total tokens: `{total_tokens}`\n"
        f"- Average response latency: `{average_latency}` ms\n"
        f"- Most talkative agent: `{top_agent}`\n"
        f"- Scheduled runs completed: `{telemetry['scheduled_runs']}`\n"
        f"- Replay views: `{telemetry['replay_views']}`\n"
        f"- Bridge events: `{telemetry['bridge_events']}`\n"
        f"- Bridge AI events: `{telemetry['bridge_ai_events']}`\n"
        f"- Observer views: `{telemetry['observer_views']}`\n"
        f"- External exports: `{telemetry['external_exports']}`\n"
        f"- External imports: `{telemetry['external_imports']}`\n"
        f"- Estimated total cost: `{format_usd(telemetry['total_estimated_cost_usd'])}`\n"
        f"- Last prompt: {telemetry['last_prompt'] or 'n/a'}"
    )



def build_schedule_status_text(config: dict[str, Any]) -> str:
    automation = config["automation"]
    status = "enabled" if automation["enabled"] else "disabled"
    next_run = automation["next_run_at"] or "n/a"
    last_run = automation["last_run_at"] or "n/a"
    active_job_name = automation.get("active_job_name") or "n/a"
    return (
        "**Autonomous Schedule**\n"
        f"- Status: `{status}`\n"
        f"- Interval seconds: `{automation['interval_seconds']}`\n"
        f"- Remaining runs: `{automation['remaining_runs']}`\n"
        f"- Run limit: `{automation['run_limit']}`\n"
        f"- Active job: `{active_job_name}`\n"
        f"- Last run at: `{last_run}`\n"
        f"- Next run at: `{next_run}`"
    )



def build_autonomous_prompt(config: dict[str, Any]) -> str:
    run_number = config["telemetry"]["scheduled_runs"] + 1
    return (
        f"Autonomous simulation run #{run_number}. "
        f"Room: {config['room_name']}. Scenario: {config['scenario']}. Mode: {config['mode']}. Topic: {config['topic']}. "
        "Advance the conversation from a fresh angle, compare tradeoffs, surface disagreements, "
        "and end with concrete next steps."
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



def save_job(config: dict[str, Any], persistent_state: dict[str, Any], raw_name: str) -> tuple[bool, str]:
    job_name = sanitize_key(raw_name)
    if not job_name:
        return False, "Job name cannot be empty."

    automation = config["automation"]
    interval_seconds = automation.get("interval_seconds") or DEFAULT_AUTOMATION_INTERVAL_SECONDS
    run_limit = automation.get("run_limit") or DEFAULT_AUTOMATION_RUNS
    persistent_state.setdefault("saved_jobs", {})[job_name] = {
        "enabled_agents": list(config["enabled_agents"]),
        "mode": config["mode"],
        "topic": config["topic"],
        "scenario": config["scenario"],
        "max_rounds": config["max_rounds"],
        "moderator_mode": config["moderator_mode"],
        "interval_seconds": interval_seconds,
        "run_limit": run_limit,
    }
    return True, f"Saved job **{job_name}**."



def load_job(
    config: dict[str, Any],
    persistent_state: dict[str, Any],
    raw_name: str,
    agent_specs: dict[str, dict[str, Any]],
) -> tuple[bool, str]:
    job_name = sanitize_key(raw_name)
    job = persistent_state.get("saved_jobs", {}).get(job_name)
    if not job:
        return False, f"Unknown job: `{raw_name}`"

    enabled_agents = [agent for agent in job.get("enabled_agents", []) if agent in agent_specs]
    if not enabled_agents:
        enabled_agents = list(agent_specs.keys())

    config["enabled_agents"] = enabled_agents
    config["mode"] = job.get("mode", DEFAULT_MODE)
    config["topic"] = job.get("topic", DEFAULT_TOPIC)
    config["scenario"] = job.get("scenario", "omni")
    config["max_rounds"] = job.get("max_rounds", DEFAULT_MAX_ROUNDS)
    config["moderator_mode"] = job.get("moderator_mode", DEFAULT_MODERATOR_MODE)
    config["automation"] = {
        "enabled": True,
        "interval_seconds": int(job.get("interval_seconds", DEFAULT_AUTOMATION_INTERVAL_SECONDS)),
        "remaining_runs": int(job.get("run_limit", DEFAULT_AUTOMATION_RUNS)),
        "run_limit": int(job.get("run_limit", DEFAULT_AUTOMATION_RUNS)),
        "last_run_at": None,
        "next_run_at": None,
        "active_job_name": job_name,
    }
    return True, f"Loaded job **{job_name}** and prepared its schedule."



def delete_job(persistent_state: dict[str, Any], raw_name: str) -> tuple[bool, str]:
    job_name = sanitize_key(raw_name)
    saved_jobs = persistent_state.get("saved_jobs", {})
    if job_name not in saved_jobs:
        return False, f"Unknown job: `{raw_name}`"

    del saved_jobs[job_name]
    return True, f"Deleted job **{job_name}**."



def save_bridge_policy(config: dict[str, Any], persistent_state: dict[str, Any], raw_name: str) -> tuple[bool, str]:
    policy_name = sanitize_key(raw_name)
    if not policy_name:
        return False, "Bridge policy name cannot be empty."
    auto_bridge = config.get("auto_bridge", {})
    if not auto_bridge.get("target_room"):
        return False, "Configure auto-bridge before saving a policy."
    persistent_state.setdefault("saved_bridge_policies", {})[policy_name] = {
        "target_room": auto_bridge.get("target_room", ""),
        "interval_prompts": auto_bridge.get("interval_prompts", 5),
        "mode": auto_bridge.get("mode", "note"),
        "role": auto_bridge.get("role", ""),
        "focus": auto_bridge.get("focus", ""),
    }
    return True, f"Saved bridge policy **{policy_name}**."



def load_bridge_policy(config: dict[str, Any], persistent_state: dict[str, Any], raw_name: str) -> tuple[bool, str]:
    policy_name = sanitize_key(raw_name)
    policy = persistent_state.get("saved_bridge_policies", {}).get(policy_name)
    if not policy:
        return False, f"Unknown bridge policy: `{raw_name}`"
    auto_bridge = config.setdefault("auto_bridge", {})
    auto_bridge["enabled"] = True
    auto_bridge["target_room"] = policy.get("target_room", "")
    auto_bridge["interval_prompts"] = int(policy.get("interval_prompts", 5))
    auto_bridge["mode"] = policy.get("mode", "note")
    auto_bridge["role"] = policy.get("role", "")
    auto_bridge["focus"] = policy.get("focus", "")
    auto_bridge["prompts_since_last"] = 0
    return True, f"Loaded bridge policy **{policy_name}**."



def delete_bridge_policy(persistent_state: dict[str, Any], raw_name: str) -> tuple[bool, str]:
    policy_name = sanitize_key(raw_name)
    policies = persistent_state.get("saved_bridge_policies", {})
    if policy_name not in policies:
        return False, f"Unknown bridge policy: `{raw_name}`"
    del policies[policy_name]
    return True, f"Deleted bridge policy **{policy_name}**."



def build_bridge_note(
    source_room_name: str,
    target_room_name: str,
    source_room_state: dict[str, Any],
    count: int,
) -> str:
    config = source_room_state.get("config", {})
    history = source_room_state.get("history", [])
    recent_entries = history[-count:]
    excerpt = " | ".join(
        render_entry(entry) for entry in recent_entries if isinstance(entry, dict)
    ) or "(no recent entries available)"
    return (
        f"Bridge from room `{source_room_name}` into `{target_room_name}`. "
        f"Scenario: {config.get('scenario', 'omni')}. Mode: {config.get('mode', DEFAULT_MODE)}. "
        f"Topic: {config.get('topic', DEFAULT_TOPIC)}. Recent activity: {excerpt}"
    )



def build_bridge_prompt(
    source_room_name: str,
    target_room_name: str,
    source_room_state: dict[str, Any],
    role: str = "",
    focus: str = "",
    count: int = 8,
) -> str:
    config = source_room_state.get("config", {})
    history = source_room_state.get("history", [])
    recent_entries = history[-count:]
    excerpt = "\n".join(
        render_entry(entry) for entry in recent_entries if isinstance(entry, dict)
    ) or "(no recent entries available)"
    
    role_instruction = BRIDGE_ROLES.get(role.lower(), "You are a generic Bridge Agent. Summarize the source room for the target room in a compact operational note.")
    requested_focus = focus or "key decisions, open risks, and what the target room should know next"
    
    return (
        f"{role_instruction}\n"
        "Produce a compact evaluation with sections: Situation, Key Insight, Risk, Recommended Follow-Up.\n\n"
        f"Source room: {source_room_name}\n"
        f"Target room: {target_room_name}\n"
        f"Source topic: {config.get('topic', DEFAULT_TOPIC)}\n"
        f"Source scenario: {config.get('scenario', 'omni')}\n"
        f"Source mode: {config.get('mode', DEFAULT_MODE)}\n"
        f"Focus: {requested_focus}\n\n"
        "Recent transcript:\n"
        f"{excerpt}"
    )



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



def build_external_room_payload(room_name: str, room_state: dict[str, Any], count: int) -> dict[str, Any]:
    config = room_state.get("config", {})
    history = room_state.get("history", [])
    recent_entries = [entry for entry in history[-count:] if isinstance(entry, dict)]
    return {
        "kind": "room_snapshot",
        "exported_at": datetime.now().isoformat(),
        "room": room_name,
        "topic": config.get("topic", DEFAULT_TOPIC),
        "scenario": config.get("scenario", "omni"),
        "mode": config.get("mode", DEFAULT_MODE),
        "enabled_agents": config.get("enabled_agents", []),
        "entries": recent_entries,
        "telemetry": config.get("telemetry", {}),
    }



def build_external_bridge_payload(
    source_room_name: str,
    target_room_name: str,
    bridge_note: str,
    source_room_state: dict[str, Any],
) -> dict[str, Any]:
    config = source_room_state.get("config", {})
    return {
        "kind": "bridge_note",
        "exported_at": datetime.now().isoformat(),
        "source_room": source_room_name,
        "target_room": target_room_name,
        "topic": config.get("topic", DEFAULT_TOPIC),
        "scenario": config.get("scenario", "omni"),
        "mode": config.get("mode", DEFAULT_MODE),
        "content": bridge_note,
    }



def write_outbox_payload(payload: dict[str, Any], outbox_dir: Path = OUTBOX_DIR) -> Path:
    outbox_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    payload_kind = sanitize_key(str(payload.get("kind", "payload"))) or "payload"
    file_path = outbox_dir / f"agentirc-{payload_kind}-{timestamp}.json"
    file_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return file_path



def list_payload_files(directory: Path, limit: int = 25) -> list[Path]:
    if not directory.exists():
        return []
    files = [path for path in directory.glob("agentirc-*.json") if path.is_file()]
    files.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return files[:limit]



def list_outbox_files(outbox_dir: Path = OUTBOX_DIR, limit: int = 25) -> list[Path]:
    return list_payload_files(outbox_dir, limit)



def list_inbox_files(inbox_dir: Path = INBOX_DIR, limit: int = 25) -> list[Path]:
    return list_payload_files(inbox_dir, limit)



def build_outbox_text(paths: list[Path]) -> str:
    if not paths:
        return "*** No external bridge payloads found in `outbox/`."
    return "**Outbox Payloads**\n" + "\n".join(f"- `{path.name}`" for path in paths)



def build_inbox_text(paths: list[Path]) -> str:
    if not paths:
        return "*** No inbound bridge payloads found in `inbox/`."
    return "**Inbox Payloads**\n" + "\n".join(f"- `{path.name}`" for path in paths)



def build_bridge_runtime_status_text() -> str:
    outbox_count = len(list_outbox_files())
    inbox_count = len(list_inbox_files())
    processed_count = len(list_payload_files(PROCESSED_DIR, limit=1000))
    return (
        "**Bridge Runtime Status**\n"
        f"- Outbox files: `{outbox_count}`\n"
        f"- Inbox files: `{inbox_count}`\n"
        f"- Processed files: `{processed_count}`\n"
        f"- Outbox directory: `{OUTBOX_DIR}`\n"
        f"- Inbox directory: `{INBOX_DIR}`\n"
        f"- Processed directory: `{PROCESSED_DIR}`"
    )



def load_external_payload(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("External payload is not a JSON object.")
    return payload



def build_imported_payload_text(payload: dict[str, Any]) -> str:
    kind = payload.get("kind", "payload")
    if kind == "room_snapshot":
        room = payload.get("room", "unknown")
        topic = payload.get("topic", DEFAULT_TOPIC)
        entries = payload.get("entries", [])
        excerpt = " | ".join(render_entry(entry) for entry in entries[-5:] if isinstance(entry, dict)) or "(no entries)"
        return f"Imported room snapshot from `{room}`. Topic: {topic}. Recent: {excerpt}"
    if kind == "bridge_note":
        source_room = payload.get("source_room", "unknown")
        target_room = payload.get("target_room", "unknown")
        content = payload.get("content", "(no content)")
        return f"Imported bridge note from `{source_room}` to `{target_room}`. {content}"
    return json.dumps(payload, ensure_ascii=False)



def list_export_files(export_dir: Path = EXPORT_DIR, limit: int = 25) -> list[Path]:
    if not export_dir.exists():
        return []
    files = [path for path in export_dir.glob("agentirc-*.json") if path.is_file()]
    files.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return files[:limit]



def build_replays_text(paths: list[Path]) -> str:
    if not paths:
        return "*** No transcript exports found in `exports/`."

    lines = []
    for path in paths:
        lines.append(f"- `{path.name}`")
    return "**Available Replays**\n" + "\n".join(lines)



def resolve_replay_file(raw_name: str, export_dir: Path = EXPORT_DIR) -> Path | None:
    available = list_export_files(export_dir, limit=200)
    if not available:
        return None

    cleaned = raw_name.strip().lower()
    if not cleaned or cleaned == "latest":
        return available[0]
    if cleaned == "previous":
        return available[1] if len(available) > 1 else None

    direct_path = export_dir / raw_name.strip()
    if direct_path.exists() and direct_path.is_file():
        return direct_path

    for path in available:
        if path.name == raw_name.strip():
            return path
    return None



def load_replay_payload(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Replay payload is not a JSON object.")
    return payload



def resolve_replay_window(total_entries: int, start_index: int, count: int) -> tuple[int, int]:
    safe_count = max(1, count)
    if total_entries <= 0:
        return 0, 0
    safe_start = max(0, min(start_index, max(0, total_entries - 1)))
    safe_end = min(total_entries, safe_start + safe_count)
    return safe_start, safe_end



def build_replay_window_text(payload: dict[str, Any], replay_name: str, start_index: int, count: int) -> str:
    history = payload.get("history", [])
    config = payload.get("config", {})
    start, end = resolve_replay_window(len(history), start_index, count)
    window_entries = history[start:end]
    lines = [render_entry(entry) for entry in window_entries if isinstance(entry, dict)]
    rendered = "\n".join(f"- `{line}`" for line in lines) if lines else "- `(no transcript lines found)`"
    return (
        f"**Replay Window: `{replay_name}`**\n"
        f"- Room: `{config.get('room_name', 'n/a')}`\n"
        f"- Topic: {config.get('topic', 'n/a')}\n"
        f"- Scenario: `{config.get('scenario', 'n/a')}`\n"
        f"- Mode: `{config.get('mode', 'n/a')}`\n"
        f"- Window: `{start}` to `{max(start, end - 1)}` of `{max(0, len(history) - 1)}`\n\n"
        f"{rendered}"
    )



def build_replay_text(payload: dict[str, Any], replay_name: str, count: int) -> str:
    history = payload.get("history", [])
    start_index = max(0, len(history) - max(1, count))
    return build_replay_window_text(payload, replay_name, start_index, count)



def build_replay_comparison_text(
    left_payload: dict[str, Any],
    left_name: str,
    right_payload: dict[str, Any],
    right_name: str,
    count: int,
) -> str:
    left_history = [render_entry(entry) for entry in left_payload.get("history", [])[-count:] if isinstance(entry, dict)]
    right_history = [render_entry(entry) for entry in right_payload.get("history", [])[-count:] if isinstance(entry, dict)]
    left_config = left_payload.get("config", {})
    right_config = right_payload.get("config", {})

    left_rendered = "\n".join(f"- `{line}`" for line in left_history) if left_history else "- `(no lines)`"
    right_rendered = "\n".join(f"- `{line}`" for line in right_history) if right_history else "- `(no lines)`"

    return (
        "**Replay Comparison**\n"
        f"- Left: `{left_name}` — scenario `{left_config.get('scenario', 'n/a')}`, mode `{left_config.get('mode', 'n/a')}`, topic {left_config.get('topic', 'n/a')}\n"
        f"- Right: `{right_name}` — scenario `{right_config.get('scenario', 'n/a')}`, mode `{right_config.get('mode', 'n/a')}`, topic {right_config.get('topic', 'n/a')}\n"
        f"- Showing last `{count}` line(s) from each replay\n\n"
        f"**Left Transcript**\n{left_rendered}\n\n"
        f"**Right Transcript**\n{right_rendered}"
    )



def export_transcript(
    history: list[dict[str, Any]],
    config: dict[str, Any],
    export_format: str,
) -> list[str]:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    file_root = EXPORT_DIR / f"agentirc-{timestamp}"
    written_paths: list[str] = []

    if export_format in {"md", "both"}:
        markdown_path = file_root.with_suffix(".md")
        markdown_lines = [
            "# AgentIRC Transcript Export",
            "",
            "## Session Configuration",
            f"- Room: `{config['room_name']}`",
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
            f"- Scheduled runs: `{config['telemetry']['scheduled_runs']}`",
            f"- Replay views: `{config['telemetry']['replay_views']}`",
            f"- Comparisons: `{config['telemetry']['comparisons']}`",
            f"- Bridge events: `{config['telemetry']['bridge_events']}`",
            f"- Bridge AI events: `{config['telemetry']['bridge_ai_events']}`",
            f"- Observer views: `{config['telemetry']['observer_views']}`",
            f"- External exports: `{config['telemetry']['external_exports']}`",
            f"- External imports: `{config['telemetry']['external_imports']}`",
            f"- Estimated cost: `{format_usd(config['telemetry']['total_estimated_cost_usd'])}`",
            f"- Actual cost: `{format_usd(config['telemetry']['total_actual_cost_usd'])}`",
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
