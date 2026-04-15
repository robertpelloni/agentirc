import os
import asyncio
import typing
import json
import httpx
import tomli
import re
from datetime import datetime, timedelta
from time import perf_counter

import chainlit as cl
from dotenv import load_dotenv

# --- Python 3.14 Compatibility Patch ---
import anyio.to_thread

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat, SelectorGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient

from bridge_connectors import build_connector_catalog_text
from simulator_tools import get_tools_by_names
from simulator_core import (
    DEFAULT_ROOM_NAME,
    EXPORT_DIR,
    MODERATOR_MODES,
    STATE_FILE,
    apply_scenario,
    append_history,
    build_agent_detail_text,
    build_agents_text,
    build_analytics_text,
    build_autonomous_prompt,
    build_bridge_note,
    build_bridge_prompt,
    build_costs_text,
    build_external_bridge_payload,
    build_external_room_payload,
    build_dashboard_text,
    build_bridge_policies_text,
    build_bridge_runtime_status_text,
    build_room_health_text,
    build_bridge_roles_text,
    build_help_text,
    build_history_text,
    build_imported_payload_text,
    build_jobs_text,
    build_leaderboard_text,
    build_archives_text,
    build_auto_bridge_status_text,
    build_judge_prompt,
    build_observer_text,
    build_lineup_text,
    build_lineups_text,
    build_moderator_modes_text,
    build_personas_text,
    build_replay_comparison_text,
    build_replay_text,
    build_replay_window_text,
    build_inbox_text,
    build_outbox_text,
    build_replays_text,
    build_room_analytics_text,
    build_room_summary_text,
    build_rooms_text,
    build_schedule_status_text,
    build_scenarios_text,
    build_status_text,
    build_telemetry_text,
    build_tools_text,
    coerce_message_content,
    configure_auto_bridge,
    configure_automation,
    create_room,
    delete_bridge_policy,
    delete_job,
    delete_lineup,
    delete_room,
    display_agent_name,
    export_transcript,
    extract_usage_metrics,
    list_export_files,
    list_inbox_files,
    list_outbox_files,
    list_room_archives,
    load_bridge_policy,
    load_external_payload,
    load_job,
    load_room_archive,
    load_lineup,
    load_persistent_state,
    load_replay_payload,
    make_default_config,
    make_entry,
    make_initial_rooms,
    parse_command,
    parse_direct_message,
    record_agent_response,
    record_bridge_ai_event,
    record_bridge_event,
    record_comparison_view,
    record_error,
    record_external_export,
    record_external_import,
    record_judge_run,
    record_observer_view,
    record_prompt_telemetry,
    record_replay_view,
    record_scheduled_run,
    render_entry,
    resolve_agent_name,
    resolve_replay_file,
    resolve_replay_window,
    save_bridge_policy,
    save_job,
    save_lineup,
    save_persistent_state,
    save_room_archive,
    set_agent_enabled,
    switch_room,
    set_moderator_mode,
    set_persona_override,
    set_rounds,
    set_tool_enabled,
    stop_auto_bridge,
    stop_automation,
    write_outbox_payload,
    resolve_room_archive,
)


async def patched_run_sync(func: typing.Callable, *args, **kwargs):
    kwargs.pop("limiter", None)
    kwargs.pop("abandon_on_cancel", None)
    return await asyncio.to_thread(func, *args, **kwargs)


anyio.to_thread.run_sync = patched_run_sync
# ---------------------------------------

load_dotenv(override=True)

LOG_FILE = "irc_session.log"
DEFAULT_EXPORT_FORMAT = "both"
SESSION_CONFIG_KEY = "config"
SESSION_TEAM_KEY = "team"
SESSION_HISTORY_KEY = "history"
SESSION_STATE_KEY = "persistent_state"
SESSION_AUTOMATION_TASK_KEY = "automation_task"
SESSION_ROOMS_KEY = "rooms"
SESSION_ROOM_KEY = "room_name"
SESSION_REPLAY_STATE_KEY = "replay_state"
JUDGE_PRICING = {"input_per_million": 0.15, "output_per_million": 0.6}

async def fetch_free_models():
    """Fetch free models from OpenRouter."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("https://openrouter.ai/api/v1/models")
            if response.status_code == 200:
                models = response.json().get("data", [])
                free_models = []
                for m in models:
                    pricing = m.get("pricing", {})
                    # Some free models have "0" as string or float
                    is_free = (
                        float(pricing.get("prompt", 1)) == 0 and 
                        float(pricing.get("completion", 1)) == 0
                    )
                    if is_free or ":free" in m.get("id", ""):
                        free_models.append({
                            "id": m.get("id"),
                            "name": m.get("name") or m.get("id"),
                            "description": m.get("description", "Free model from OpenRouter.")
                        })
                return free_models
    except Exception as e:
        print(f"Failed to fetch free models: {e}")
    return []

async def identify_model_nick(model_id: str, base_url: str | None = None) -> str:
    """Ask a model for its name and return the first word."""
    client = get_client(model_id, base_url_override=base_url)
    prompt = "What is your name? Respond with your model name only, no punctuation."
    try:
        response = await client.create(
            messages=[{"role": "user", "content": prompt}]
        )
        content = response.choices[0].message.content.strip()
        # Clean and get first word
        words = re.findall(r"\w+", content)
        if words:
            return words[0].capitalize()
    except Exception:
        pass
    # Fallback to sanitized ID part if name check fails
    return model_id.split("/")[-1].split(":")[0].replace("-", "").replace(".", "").capitalize()

def update_agent_specs(new_specs: dict):
    cl.user_session.set("agent_specs", new_specs)
    # Sync to persistent state as well
    ps = get_persistent_state()
    ps["agent_specs"] = new_specs
    persist_state()

def load_agents_config():
    return {}

AGENT_SPECS = load_agents_config()

def load_global_config():
    if os.path.exists("config.toml"):
        with open("config.toml", "rb") as f:
            return tomli.load(f)
    return {}

GLOBAL_CONFIG = load_global_config()


def log_irc(message: str):
    with open(LOG_FILE, "a", encoding="utf-8") as handle:
        handle.write(f"{message}\n")



def get_client(model_name: str, base_url_override: str | None = None):
    provider_config = GLOBAL_CONFIG.get("provider", {})
    base_url = base_url_override or provider_config.get("base_url", "https://openrouter.ai/api/v1")
    api_key_env = provider_config.get("api_key_env", "OPENROUTER_API_KEY")
    
    # Handle specific provider env vars if they exist
    api_key = None
    if base_url and "kilo.ai" in base_url:
        api_key = os.environ.get("KILOCODE_API_KEY")
    elif base_url and "cline.bot" in base_url:
        api_key = os.environ.get("CLINE_API_KEY")
    
    if not api_key:
        api_key = os.environ.get(api_key_env)

    # Some providers like Kilo/Cline might just use 'free' as the model name at their endpoint
    # but we'll try the provided name first.
    return OpenAIChatCompletionClient(
        model=model_name,
        api_key=api_key,
        base_url=base_url,
        model_info={
            "vision": False,
            "function_calling": True,
            "json_output": True,
            "structured_output": True,
            "family": "unknown",
        },
    )




def get_agent_specs():
    return cl.user_session.get("agent_specs", {})

def get_config() -> dict:
    return cl.user_session.get(SESSION_CONFIG_KEY)



def get_history() -> list[dict]:
    history = cl.user_session.get(SESSION_HISTORY_KEY)
    if history is None:
        history = []
        cl.user_session.set(SESSION_HISTORY_KEY, history)
    return history



def save_history(history: list[dict]):
    cl.user_session.set(SESSION_HISTORY_KEY, history)



def get_persistent_state() -> dict:
    state = cl.user_session.get(SESSION_STATE_KEY)
    if state is None:
        state = load_persistent_state(STATE_FILE)
        # Ensure agent_specs is initialized if missing
        if "agent_specs" not in state:
            state["agent_specs"] = {}
        cl.user_session.set(SESSION_STATE_KEY, state)
    return state



def get_rooms() -> dict[str, dict]:
    rooms = cl.user_session.get(SESSION_ROOMS_KEY)
    if rooms is None:
        rooms = make_initial_rooms(agent_specs, get_persistent_state())
        cl.user_session.set(SESSION_ROOMS_KEY, rooms)
    return rooms



def get_current_room_name() -> str:
    room_name = cl.user_session.get(SESSION_ROOM_KEY)
    if room_name is None:
        room_name = DEFAULT_ROOM_NAME
        cl.user_session.set(SESSION_ROOM_KEY, room_name)
    return room_name



def save_current_room_state():
    rooms = get_rooms()
    room_name = get_current_room_name()
    rooms[room_name] = {
        "config": get_config(),
        "history": get_history(),
    }
    cl.user_session.set(SESSION_ROOMS_KEY, rooms)



def activate_room(room_name: str):
    rooms = get_rooms()
    room_state = rooms[room_name]
    cl.user_session.set(SESSION_ROOM_KEY, room_name)
    cl.user_session.set(SESSION_CONFIG_KEY, room_state["config"])
    cl.user_session.set(SESSION_HISTORY_KEY, room_state["history"])
    rebuild_team()



def append_entry_to_room(
    room_name: str,
    author: str,
    content: str,
    kind: str = "message",
    target: str | None = None,
) -> dict:
    rooms = get_rooms()
    room_state = rooms[room_name]
    history = room_state["history"]
    entry = append_history(history, make_entry(author=author, content=content, kind=kind, target=target))
    room_state["history"] = history
    log_irc(render_entry(entry))
    if room_name == get_current_room_name():
        cl.user_session.set(SESSION_HISTORY_KEY, history)
    cl.user_session.set(SESSION_ROOMS_KEY, rooms)
    return entry



def persist_state():
    state = get_persistent_state()
    save_persistent_state(state, STATE_FILE)



def get_automation_task() -> asyncio.Task | None:
    return cl.user_session.get(SESSION_AUTOMATION_TASK_KEY)



def set_automation_task(task: asyncio.Task | None):
    cl.user_session.set(SESSION_AUTOMATION_TASK_KEY, task)



def get_replay_state() -> dict | None:
    return cl.user_session.get(SESSION_REPLAY_STATE_KEY)



def set_replay_state(state: dict | None):
    cl.user_session.set(SESSION_REPLAY_STATE_KEY, state)


async def stop_automation_task():
    task = get_automation_task()
    set_automation_task(None)
    if task and not task.done():
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass



def add_history_entry(author: str, content: str, kind: str = "message", target: str | None = None) -> dict:
    history = get_history()
    entry = append_history(history, make_entry(author=author, content=content, kind=kind, target=target))
    save_history(history)
    log_irc(render_entry(entry))
    return entry


async def send_system_notice(content: str):
    add_history_entry(author="system", content=content, kind="system")
    await cl.Message(content=f"*** {content}").send()



def create_team(config: dict):
    enabled_agents = config["enabled_agents"]
    agents = []
    specs = get_agent_specs()

    for name in enabled_agents:
        spec = specs.get(name)
        if not spec:
            continue
        peers = [display_agent_name(peer) for peer in enabled_agents if peer != name]
        persona = config.get("persona_overrides", {}).get(name, spec["bio"])
        system_message = (
            f"You are {display_agent_name(name)}. You are speaking as yourself with your own personality developed through training. "
            "Do NOT simulate a fake IRC conversation or simulate multiple users. You are in an IRC chat room but you are just one participant. "
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
            model_client=get_client(spec["model"], base_url_override=spec.get("base_url")),
            system_message=system_message,
            tools=get_tools_by_names(config.get("enabled_tools", [])) or None,
        )
        agents.append(agent)

    if config["mode"] == "broadcast":
        termination = MaxMessageTermination(len(agents) + 1)
        return RoundRobinGroupChat(agents, termination_condition=termination)

    termination = TextMentionTermination("TERMINATE") | MaxMessageTermination(config["max_rounds"])
    selector_client = get_client("openrouter/auto")
    return SelectorGroupChat(agents, model_client=selector_client, termination_condition=termination)



def create_judge_agent(config: dict):
    return AssistantAgent(
        name="Judge",
        model_client=get_client(config["judge_model"]),
        system_message=(
            "You are the neutral Judge for an IRC-style multi-model simulator. "
            "Produce compact, readable evaluations with practical next-step guidance."
        ),
    )



def create_bridge_agent(config: dict):
    return AssistantAgent(
        name="BridgeAgent",
        model_client=get_client(config["judge_model"]),
        system_message=(
            "You are a cross-room Bridge Agent for an IRC-style multi-model simulator. "
            "Create concise, high-signal bridge notes for other rooms."
        ),
    )



def rebuild_team():
    config = get_config()
    team = create_team(config)
    cl.user_session.set(SESSION_TEAM_KEY, team)
    return team



def format_export_result(paths: list[str]) -> str:
    if not paths:
        return "No export files were created."
    joined = "\n".join(f"- `{path}`" for path in paths)
    return f"Transcript export completed:\n{joined}"


async def execute_bridge(source_room_name: str, target_room_name: str, count: int) -> bool:
    changed, response, resolved_source = switch_room(get_rooms(), source_room_name)
    if not changed or resolved_source is None:
        await send_system_notice(response)
        return False
    changed, response, resolved_target = switch_room(get_rooms(), target_room_name)
    if not changed or resolved_target is None:
        await send_system_notice(response)
        return False
    bridge_note = build_bridge_note(resolved_source, resolved_target, get_rooms()[resolved_source], count)
    append_entry_to_room(resolved_target, author="system", content=bridge_note, kind="system")
    record_bridge_event(get_rooms()[resolved_target]["config"])
    if resolved_target == get_current_room_name():
        await cl.Message(content=f"*** {bridge_note}").send()
    else:
        await send_system_notice(
            f"Delivered bridge summary from **{resolved_source}** to **{resolved_target}**."
        )
    return True


async def execute_bridge_ai(source_room_name: str, target_room_name: str, role: str, focus: str) -> bool:
    changed, response, resolved_source = switch_room(get_rooms(), source_room_name)
    if not changed or resolved_source is None:
        await send_system_notice(response)
        return False
    changed, response, resolved_target = switch_room(get_rooms(), target_room_name)
    if not changed or resolved_target is None:
        await send_system_notice(response)
        return False

    bridge_prompt = build_bridge_prompt(
        resolved_source,
        resolved_target,
        get_rooms()[resolved_source],
        role,
        focus,
    )
    bridge_agent = create_bridge_agent(get_config())
    await send_system_notice(
        f"Bridge agent summarizing **{resolved_source}** for **{resolved_target}**..."
    )

    bridge_content = ""
    bridge_usage = None
    start_time = perf_counter()
    async for event in bridge_agent.run_stream(task=bridge_prompt):
        source = getattr(event, "source", None)
        content = coerce_message_content(getattr(event, "content", None))
        if not source or not content or source.lower() == "user":
            continue
        bridge_content = content
        bridge_usage = extract_usage_metrics(event)

    if not bridge_content:
        await send_system_notice("Bridge agent did not return a usable summary.")
        return False

    target_config = get_rooms()[resolved_target]["config"]
    record_bridge_ai_event(target_config, bridge_prompt)
    record_bridge_event(target_config)
    record_agent_response(
        target_config,
        "BridgeAgent",
        bridge_prompt,
        bridge_content,
        round((perf_counter() - start_time) * 1000, 2),
        pricing=JUDGE_PRICING,
        usage=bridge_usage,
    )
    entry = append_entry_to_room(resolved_target, author="BridgeAgent", content=bridge_content, kind="message")
    if resolved_target == get_current_room_name():
        await cl.Message(author="BridgeAgent", content=render_entry(entry)).send()
    else:
        await send_system_notice(
            f"Delivered AI bridge note from **{resolved_source}** to **{resolved_target}**."
        )
    return True


async def maybe_run_auto_bridge():
    config = get_config()
    auto_bridge = config.get("auto_bridge", {})
    if not auto_bridge.get("enabled"):
        return
    auto_bridge["prompts_since_last"] = auto_bridge.get("prompts_since_last", 0) + 1
    if auto_bridge["prompts_since_last"] < auto_bridge.get("interval_prompts", 1):
        return
    auto_bridge["prompts_since_last"] = 0
    target_room = auto_bridge.get("target_room") or ""
    if not target_room:
        return
    source_room = get_current_room_name()
    if target_room == source_room:
        return
    if auto_bridge.get("mode") == "ai":
        await execute_bridge_ai(source_room, target_room, auto_bridge.get("role", ""), auto_bridge.get("focus", ""))
    else:
        await execute_bridge(source_room, target_room, 5)


async def run_automation_loop():
    try:
        while True:
            config = get_config()
            automation = config["automation"]
            if not automation["enabled"] or automation["remaining_runs"] <= 0:
                break

            next_run_at = datetime.now() + timedelta(seconds=automation["interval_seconds"])
            automation["next_run_at"] = next_run_at.isoformat()
            await asyncio.sleep(automation["interval_seconds"])

            config = get_config()
            automation = config["automation"]
            if not automation["enabled"] or automation["remaining_runs"] <= 0:
                break

            automation["remaining_runs"] -= 1
            automation["next_run_at"] = None
            prompt = build_autonomous_prompt(config)
            record_scheduled_run(config, prompt)
            await send_system_notice(
                f"Autonomous run starting ({automation['run_limit'] - automation['remaining_runs']}/{automation['run_limit']})."
            )
            team = cl.user_session.get(SESSION_TEAM_KEY)
            await stream_agent(team, prompt, count_prompt_telemetry=False)

        config = get_config()
        automation = config["automation"]
        automation["enabled"] = False
        automation["remaining_runs"] = 0
        automation["run_limit"] = 0
        automation["next_run_at"] = None
        automation["active_job_name"] = None
        await send_system_notice("Autonomous schedule completed.")
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        record_error(get_config())
        await send_system_notice(f"Autonomous schedule failed: {exc}")
    finally:
        set_automation_task(None)


async def handle_command(command: str, args: str) -> bool:
    config = get_config()
    persistent_state = get_persistent_state()

    if command == "/help":
        await cl.Message(content=build_help_text()).send()
        return True

    if command == "/slap":
        target = args if args else "someone"
        content = f"* {config['nick']} slaps {target} around a bit with a large trout"
        add_history_entry(author="system", content=content, kind="system")
        await cl.Message(author="system", content=content).send()
        # Feed it to the models
        await stream_agent(
            cl.user_session.get(SESSION_TEAM_KEY),
            content,
            telemetry_name="system"
        )
        return True

    if command == "/me":
        content = f"* {config['nick']} {args}"
        add_history_entry(author="system", content=content, kind="system")
        await cl.Message(author="system", content=content).send()
        # Feed it to the models
        await stream_agent(
            cl.user_session.get(SESSION_TEAM_KEY),
            content,
            telemetry_name="system"
        )
        return True

    if command == "/mode":
        new_mode = args.lower()
        if new_mode not in {"broadcast", "discuss"}:
            await send_system_notice("Usage: `/mode broadcast` or `/mode discuss`")
            return True
        config["mode"] = new_mode
        rebuild_team()

        await send_system_notice(f"Mode changed to **{new_mode.upper()}**.")
        return True

    if command == "/topic":
        if not args:
            await send_system_notice(f"Current topic: {config['topic']}")
            return True
        config["topic"] = args
        await update_settings_ui()
        await send_system_notice(f"Topic changed to: {args}")
        return True
        config["topic"] = args
        rebuild_team()
        await update_settings_ui()
        await send_system_notice(f"Topic changed to: {args}")
        return True

    if command == "/nick":
        if not args:
            await send_system_notice(f"Current nick: {config['nick']}")
            return True
        config["nick"] = args
        await send_system_notice(f"Your nick is now **{args}**.")
        return True

    if command == "/slap":
        target = args if args else "someone"
        nick = config.get('nick', 'operator')
        action_msg = f"* {nick} slaps {target} around a bit with a large trout"
        await send_system_notice(action_msg)
        add_history_entry(author="system", content=action_msg, kind="system")
        return True

    if command == "/status":
        await cl.Message(content=build_status_text(config, len(get_history()), persistent_state)).send()
        return True

    if command == "/dashboard":
        await cl.Message(content=build_dashboard_text(get_rooms(), get_current_room_name(), persistent_state)).send()
        return True

    if command == "/observer":
        record_observer_view(config)
        await cl.Message(content=build_observer_text(get_rooms(), get_current_room_name())).send()
        return True

    if command == "/health":
        await cl.Message(content=build_room_health_text(get_rooms(), get_current_room_name())).send()
        return True

    if command == "/leaderboard":
        await cl.Message(content=build_leaderboard_text(get_rooms(), get_agent_specs())).send()
        return True

    if command == "/room-summary":
        count = 3
        if args:
            try:
                count = max(1, min(10, int(args)))
            except ValueError:
                await send_system_notice("Room summary count must be an integer between 1 and 10.")
                return True
        await cl.Message(content=build_room_summary_text(get_rooms(), count)).send()
        return True

    if command == "/room-analytics":
        room_name = get_current_room_name()
        if args:
            changed, response, resolved_room_name = switch_room(get_rooms(), args)
            if not changed or resolved_room_name is None:
                await send_system_notice(response)
                return True
            room_name = resolved_room_name
        await cl.Message(content=build_room_analytics_text(room_name, get_rooms()[room_name], get_agent_specs())).send()
        return True

    if command == "/bridge":
        parts = args.split()
        if len(parts) < 2:
            await send_system_notice("Usage: `/bridge <source> <target> [count]`")
            return True
        source_room_name = parts[0]
        target_room_name = parts[1]
        count = 5
        if len(parts) > 2:
            try:
                count = max(1, min(20, int(parts[2])))
            except ValueError:
                await send_system_notice("Bridge count must be an integer between 1 and 20.")
                return True
        await execute_bridge(source_room_name, target_room_name, count)
        return True

    if command == "/bridge-ai":
        parts = args.split(" ", 3)
        if len(parts) < 2:
            await send_system_notice("Usage: `/bridge-ai <source> <target> [role] [focus]`")
            return True
        source_room_name = parts[0]
        target_room_name = parts[1]
        role = parts[2] if len(parts) > 2 else ""
        focus = parts[3] if len(parts) > 3 else ""
        await execute_bridge_ai(source_room_name, target_room_name, role, focus)
        return True

    if command == "/bridge-export":
        parts = args.split()
        room_name = parts[0] if parts else get_current_room_name()
        count = 10
        if len(parts) > 1:
            try:
                count = max(1, min(100, int(parts[1])))
            except ValueError:
                await send_system_notice("Bridge export count must be an integer between 1 and 100.")
                return True
        changed, response, resolved_room_name = switch_room(get_rooms(), room_name)
        if not changed or resolved_room_name is None:
            await send_system_notice(response)
            return True
        room_state = get_rooms()[resolved_room_name]
        payload = build_external_room_payload(resolved_room_name, room_state, count)
        outbox_path = write_outbox_payload(payload)
        record_external_export(room_state["config"])
        await send_system_notice(f"Exported room payload to `{outbox_path}`.")
        return True

    if command == "/auto-bridge":
        if not args:
            await cl.Message(content=build_auto_bridge_status_text(config)).send()
            return True
        if args.lower() == "stop":
            await send_system_notice(stop_auto_bridge(config))
            return True
        parts = args.split(" ", 4)
        if len(parts) < 2:
            await send_system_notice("Usage: `/auto-bridge <target> <interval> [note|ai] [role] [focus]`")
            return True
        target_room = parts[0]
        interval_text = parts[1]
        mode = parts[2] if len(parts) > 2 else "note"
        role = parts[3] if len(parts) > 3 else ""
        focus = parts[4] if len(parts) > 4 else ""
        changed, response = configure_auto_bridge(config, target_room, interval_text, mode, role, focus)
        await send_system_notice(response)
        return True

    if command == "/bridge-policies":
        await cl.Message(content=build_bridge_policies_text(persistent_state)).send()
        return True

    if command == "/save-bridge-policy":
        if not args:
            await send_system_notice("Usage: `/save-bridge-policy <name>`")
            return True
        changed, response = save_bridge_policy(config, persistent_state, args)
        if changed:
            persist_state()
        await send_system_notice(response)
        return True

    if command == "/load-bridge-policy":
        if not args:
            await send_system_notice("Usage: `/load-bridge-policy <name>`")
            return True
        changed, response = load_bridge_policy(config, persistent_state, args)
        await send_system_notice(response)
        return True

    if command == "/delete-bridge-policy":
        if not args:
            await send_system_notice("Usage: `/delete-bridge-policy <name>`")
            return True
        changed, response = delete_bridge_policy(persistent_state, args)
        if changed:
            persist_state()
        await send_system_notice(response)
        return True

    if command == "/archives":
        await cl.Message(content=build_archives_text(list_room_archives())).send()
        return True

    if command == "/archive-room":
        archive_name = args.strip() or get_current_room_name()
        room_state = get_rooms()[get_current_room_name()]
        path = save_room_archive(archive_name, room_state)
        await send_system_notice(f"Archived room to `{path}`.")
        return True

    if command == "/restore-room":
        parts = args.split()
        if not parts:
            await send_system_notice("Usage: `/restore-room <archive> [room]`")
            return True
        archive_path = resolve_room_archive(parts[0])
        if archive_path is None:
            await send_system_notice("Room archive not found.")
            return True
        payload = load_room_archive(archive_path)
        room_name = parts[1] if len(parts) > 1 else payload.get("room_name", get_current_room_name())
        save_current_room_state()
        changed, response, resolved_room = create_room(get_rooms(), room_name, get_agent_specs(), persistent_state)
        if not changed and resolved_room is None:
            switched, _, resolved_room = switch_room(get_rooms(), room_name)
            if not switched or resolved_room is None:
                await send_system_notice(response)
                return True
        get_rooms()[resolved_room] = payload["room_state"]
        await stop_automation_task()
        activate_room(resolved_room)
        await send_system_notice(f"Restored archive `{archive_path.name}` into room **{resolved_room}**.")
        return True

    if command == "/bridge-runtime":
        await cl.Message(content=build_bridge_runtime_status_text()).send()
        return True

    if command == "/connectors":
        await cl.Message(content=build_connector_catalog_text()).send()
        return True

    if command == "/outbox":
        await cl.Message(content=build_outbox_text(list_outbox_files())).send()
        return True

    if command == "/inbox":
        await cl.Message(content=build_inbox_text(list_inbox_files())).send()
        return True

    if command == "/import-bridge":
        parts = args.split()
        if not parts:
            await send_system_notice("Usage: `/import-bridge <file> [room]`")
            return True
        file_name = parts[0]
        target_room_name = parts[1] if len(parts) > 1 else get_current_room_name()
        inbox_files = {path.name: path for path in list_inbox_files(limit=200)}
        payload_path = inbox_files.get(file_name)
        if payload_path is None:
            await send_system_notice("Inbox payload not found.")
            return True
        changed, response, resolved_target = switch_room(get_rooms(), target_room_name)
        if not changed or resolved_target is None:
            await send_system_notice(response)
            return True
        payload = load_external_payload(payload_path)
        imported_text = build_imported_payload_text(payload)
        append_entry_to_room(resolved_target, author="system", content=imported_text, kind="system")
        record_external_import(get_rooms()[resolved_target]["config"])
        if resolved_target == get_current_room_name():
            await cl.Message(content=f"*** {imported_text}").send()
        else:
            await send_system_notice(f"Imported `{file_name}` into **{resolved_target}**.")
        return True

    if command == "/bridge-roles":
        await cl.Message(content=build_bridge_roles_text()).send()
        return True

    if command == "/tools":
        await cl.Message(content=build_tools_text(config)).send()
        return True

    if command in {"/enable-tool", "/disable-tool"}:
        if not args:
            await send_system_notice(f"Usage: `{command} <tool>`")
            return True
        changed, response = set_tool_enabled(config, args, enabled=command == "/enable-tool")
        if changed:
            rebuild_team()
        await update_settings_ui()
        await send_system_notice(response)
        return True

    if command == "/rooms":
        await cl.Message(content=build_rooms_text(get_rooms(), get_current_room_name())).send()
        return True

    if command == "/room":
        if not args:
            await send_system_notice(f"Current room: **{get_current_room_name()}**")
            return True
        save_current_room_state()
        changed, response, room_name = switch_room(get_rooms(), args)
        if not changed or room_name is None:
            await send_system_notice(response)
            return True
        await stop_automation_task()
        activate_room(room_name)
        await send_system_notice(response)
        return True

    if command == "/new-room":
        if not args:
            await send_system_notice("Usage: `/new-room <name>`")
            return True
        save_current_room_state()
        changed, response, room_name = create_room(get_rooms(), args, get_agent_specs(), persistent_state)
        if not changed or room_name is None:
            await send_system_notice(response)
            return True
        await stop_automation_task()
        activate_room(room_name)
        await send_system_notice(f"{response} Switched to **{room_name}**.")
        return True

    if command == "/delete-room":
        if not args:
            await send_system_notice("Usage: `/delete-room <name>`")
            return True
        save_current_room_state()
        changed, response, next_room_name = delete_room(get_rooms(), get_current_room_name(), args)
        if not changed:
            await send_system_notice(response)
            return True
        await stop_automation_task()
        if next_room_name:
            activate_room(next_room_name)
        await send_system_notice(response)
        return True

    if command == "/lineup":
        await cl.Message(content=build_lineup_text(get_agent_specs(), config["enabled_agents"])).send()
        return True

    if command == "/agents":
        await cl.Message(content=build_agents_text(get_agent_specs(), config["enabled_agents"], config)).send()
        return True

    if command == "/whois":
        if not args:
            await send_system_notice("Usage: `/whois <agent>`")
            return True
        agent_name = resolve_agent_name(args, list(get_agent_specs().keys()))
        if not agent_name:
            await send_system_notice(f"Unknown agent: `{args}`")
            return True
        await cl.Message(content=build_agent_detail_text(agent_name, get_agent_specs(), config["enabled_agents"], config)).send()
        return True

    if command in {"/enable", "/disable"}:
        if not args:
            await send_system_notice(f"Usage: `{command} <agent>`")
            return True
        changed, response = set_agent_enabled(
            config=config,
            raw_name=args,
            enabled=command == "/enable",
            agent_specs=get_agent_specs(),
        )
        if changed:
            rebuild_team()
            await update_settings_ui()
        await send_system_notice(response)
        return True
        changed, response = set_agent_enabled(
            config=config,
            raw_name=args,
            enabled=command == "/enable",
            agent_specs=get_agent_specs(),
        )
        if changed:
            rebuild_team()
        await update_settings_ui()
        await send_system_notice(response)
        return True

    if command == "/rounds":
        if not args:
            await send_system_notice(f"Current discuss-mode max rounds: {config['max_rounds']}")
            return True
        changed, response = set_rounds(config, args)
        if changed and config["mode"] == "discuss":
            rebuild_team()
        await update_settings_ui()
        await send_system_notice(response)
        return True

    if command == "/scenario":
        if not args:
            await cl.Message(content=build_scenarios_text()).send()
            return True
        changed, response = apply_scenario(config, args, get_agent_specs())
        if changed:
            rebuild_team()
        await update_settings_ui()
        await send_system_notice(response)
        return True

    if command == "/moderator":
        if not args:
            await cl.Message(content=build_moderator_modes_text()).send()
            return True
        changed, response = set_moderator_mode(config, args)
        if changed:
            rebuild_team()
        await update_settings_ui()
        await send_system_notice(response)
        return True

    if command == "/telemetry":
        await cl.Message(content=build_telemetry_text(config, get_agent_specs())).send()
        return True

    if command == "/analytics":
        await cl.Message(content=build_analytics_text(config, get_history(), get_agent_specs())).send()
        return True

    if command == "/costs":
        await cl.Message(content=build_costs_text(config, get_agent_specs())).send()
        return True

    if command == "/judge":
        if not get_history():
            await send_system_notice("Judge evaluation requires transcript history.")
            return True
        judge_agent = create_judge_agent(config)
        judge_prompt = build_judge_prompt(get_history(), config, args)
        record_judge_run(config, judge_prompt)
        await send_system_notice(f"Judge model `{config['judge_model']}` evaluating the recent transcript...")
        await stream_agent(
            judge_agent,
            judge_prompt,
            telemetry_name="Judge",
            pricing=JUDGE_PRICING,
            count_prompt_telemetry=False,
        )
        return True

    if command == "/personas":
        await cl.Message(content=build_personas_text(config, get_agent_specs())).send()
        return True

    if command == "/persona":
        if not args:
            await send_system_notice("Usage: `/persona <agent> <text>` or `/persona clear <agent>`")
            return True

        if args.lower().startswith("clear "):
            clear_target = args.split(" ", 1)[1].strip()
            changed, response = set_persona_override(config, persistent_state, clear_target, "", get_agent_specs())
        else:
            parts = args.split(" ", 1)
            if len(parts) < 2:
                await send_system_notice("Usage: `/persona <agent> <text>` or `/persona clear <agent>`")
                return True
            changed, response = set_persona_override(config, persistent_state, parts[0], parts[1], get_agent_specs())

        if changed:
            persist_state()
            rebuild_team()
        await update_settings_ui()
        await send_system_notice(response)
        return True

    if command == "/lineups":
        await cl.Message(content=build_lineups_text(persistent_state)).send()
        return True

    if command == "/save-lineup":
        if not args:
            await send_system_notice("Usage: `/save-lineup <name>`")
            return True
        changed, response = save_lineup(config, persistent_state, args)
        if changed:
            persist_state()
        await send_system_notice(response)
        return True

    if command == "/load-lineup":
        if not args:
            await send_system_notice("Usage: `/load-lineup <name>`")
            return True
        changed, response = load_lineup(config, persistent_state, args, get_agent_specs())
        if changed:
            rebuild_team()
        await update_settings_ui()
        await send_system_notice(response)
        return True

    if command == "/delete-lineup":
        if not args:
            await send_system_notice("Usage: `/delete-lineup <name>`")
            return True
        changed, response = delete_lineup(persistent_state, args)
        if changed:
            persist_state()
        await send_system_notice(response)
        return True

    if command == "/jobs":
        await cl.Message(content=build_jobs_text(persistent_state)).send()
        return True

    if command == "/bridge-policies":
        await cl.Message(content=build_bridge_policies_text(persistent_state)).send()
        return True

    if command == "/save-bridge-policy":
        if not args:
            await send_system_notice("Usage: `/save-bridge-policy <name>`")
            return True
        changed, response = save_bridge_policy(config, persistent_state, args)
        if changed:
            persist_state()
        await send_system_notice(response)
        return True

    if command == "/load-bridge-policy":
        if not args:
            await send_system_notice("Usage: `/load-bridge-policy <name>`")
            return True
        changed, response = load_bridge_policy(config, persistent_state, args)
        await send_system_notice(response)
        return True

    if command == "/delete-bridge-policy":
        if not args:
            await send_system_notice("Usage: `/delete-bridge-policy <name>`")
            return True
        changed, response = delete_bridge_policy(persistent_state, args)
        if changed:
            persist_state()
        await send_system_notice(response)
        return True

    if command == "/save-job":
        if not args:
            await send_system_notice("Usage: `/save-job <name>`")
            return True
        changed, response = save_job(config, persistent_state, args)
        if changed:
            persist_state()
        await send_system_notice(response)
        return True

    if command == "/run-job":
        if not args:
            await send_system_notice("Usage: `/run-job <name>`")
            return True
        changed, response = load_job(config, persistent_state, args, get_agent_specs())
        if changed:
            rebuild_team()
            await update_settings_ui()
            await stop_automation_task()
            task = asyncio.create_task(run_automation_loop())
            set_automation_task(task)
        await send_system_notice(response)
        return True

    if command == "/delete-job":
        if not args:
            await send_system_notice("Usage: `/delete-job <name>`")
            return True
        changed, response = delete_job(persistent_state, args)
        if changed:
            persist_state()
        await send_system_notice(response)
        return True

    if command == "/schedule":
        if not args:
            await cl.Message(content=build_schedule_status_text(config)).send()
            return True

        if args.lower() == "stop":
            await stop_automation_task()
            await send_system_notice(stop_automation(config))
            return True

        parts = args.split()
        interval_text = parts[0]
        runs_text = parts[1] if len(parts) > 1 else None
        changed, response = configure_automation(config, interval_text, runs_text)
        if not changed:
            await send_system_notice(response)
            return True

        await stop_automation_task()
        task = asyncio.create_task(run_automation_loop())
        set_automation_task(task)
        await send_system_notice(response)
        return True

    if command == "/replays":
        await cl.Message(content=build_replays_text(list_export_files(EXPORT_DIR))).send()
        return True

    if command == "/replay":
        parts = args.split()
        replay_name = parts[0] if parts else "latest"
        count = 12
        if len(parts) > 1:
            try:
                count = max(1, min(100, int(parts[1])))
            except ValueError:
                await send_system_notice("Replay line count must be an integer between 1 and 100.")
                return True
        replay_path = resolve_replay_file(replay_name, EXPORT_DIR)
        if replay_path is None:
            await send_system_notice("No matching replay export found.")
            return True
        payload = load_replay_payload(replay_path)
        record_replay_view(config)
        await cl.Message(content=build_replay_text(payload, replay_path.name, count)).send()
        return True

    if command == "/replay-open":
        parts = args.split()
        replay_name = parts[0] if parts else "latest"
        count = 8
        if len(parts) > 1:
            try:
                count = max(1, min(100, int(parts[1])))
            except ValueError:
                await send_system_notice("Replay window count must be an integer between 1 and 100.")
                return True
        replay_path = resolve_replay_file(replay_name, EXPORT_DIR)
        if replay_path is None:
            await send_system_notice("No matching replay export found.")
            return True
        payload = load_replay_payload(replay_path)
        set_replay_state({"name": replay_path.name, "payload": payload, "index": 0, "count": count})
        record_replay_view(config)
        await cl.Message(content=build_replay_window_text(payload, replay_path.name, 0, count)).send()
        return True

    if command == "/replay-step":
        replay_state = get_replay_state()
        if not replay_state:
            await send_system_notice("No replay is currently open. Use `/replay-open` first.")
            return True
        parts = args.split()
        action = parts[0].lower() if parts else "next"
        count = replay_state.get("count", 8)
        if len(parts) > 1:
            try:
                count = max(1, min(100, int(parts[1])))
            except ValueError:
                await send_system_notice("Replay window count must be an integer between 1 and 100.")
                return True

        payload = replay_state["payload"]
        history = payload.get("history", [])
        current_index = replay_state.get("index", 0)
        if action == "next":
            new_index = current_index + count
        elif action == "prev":
            new_index = current_index - count
        elif action == "start":
            new_index = 0
        elif action == "end":
            new_index = max(0, len(history) - count)
        else:
            try:
                new_index = int(action)
            except ValueError:
                await send_system_notice("Usage: `/replay-step [next|prev|start|end|index] [count]`")
                return True

        new_index, _ = resolve_replay_window(len(history), new_index, count)
        replay_state["index"] = new_index
        replay_state["count"] = count
        set_replay_state(replay_state)
        record_replay_view(config)
        await cl.Message(content=build_replay_window_text(payload, replay_state["name"], new_index, count)).send()
        return True

    if command == "/compare":
        parts = args.split()
        if len(parts) < 2:
            await send_system_notice("Usage: `/compare <left> <right> [count]`")
            return True
        left_name = parts[0]
        right_name = parts[1]
        count = 10
        if len(parts) > 2:
            try:
                count = max(1, min(100, int(parts[2])))
            except ValueError:
                await send_system_notice("Comparison line count must be an integer between 1 and 100.")
                return True
        left_path = resolve_replay_file(left_name, EXPORT_DIR)
        right_path = resolve_replay_file(right_name, EXPORT_DIR)
        if left_path is None or right_path is None:
            await send_system_notice("One or both replay exports could not be resolved.")
            return True
        left_payload = load_replay_payload(left_path)
        right_payload = load_replay_payload(right_path)
        record_comparison_view(config)
        await cl.Message(
            content=build_replay_comparison_text(
                left_payload,
                left_path.name,
                right_payload,
                right_path.name,
                count,
            )
        ).send()
        return True

    if command == "/history":
        count = 10
        if args:
            try:
                count = max(1, min(50, int(args)))
            except ValueError:
                await send_system_notice("History count must be an integer between 1 and 50.")
                return True
        await cl.Message(content=build_history_text(get_history(), count)).send()
        return True

    if command == "/export":
        export_format = args.lower() if args else DEFAULT_EXPORT_FORMAT
        if export_format not in {"md", "json", "both"}:
            await send_system_notice("Usage: `/export [md|json|both]`")
            return True
        paths = export_transcript(get_history(), config, export_format)
        await send_system_notice(format_export_result(paths))
        return True

    if command == "/clear":
        save_history([])
        save_current_room_state()
        await send_system_notice("Transcript buffer cleared for this room.")
        return True

    if command == "/reset":
        await stop_automation_task()
        room_name = get_current_room_name()
        cl.user_session.set(SESSION_CONFIG_KEY, make_default_config(get_agent_specs(), persistent_state, room_name=room_name))
        save_history([])
        save_current_room_state()
        rebuild_team()
        await update_settings_ui()
        await send_system_notice("Current room state reset to defaults.")
        return True

    await send_system_notice(f"Unknown command: `{command}`. Use `/help`.")
    return True


async def stream_agent(
    agent_or_team,
    prompt: str,
    target_name: str | None = None,
    telemetry_name: str | None = None,
    pricing: dict | None = None,
    count_prompt_telemetry: bool = True,
):
    config = get_config()
    is_direct_message = target_name is not None
    config["simulation_count"] += 1
    if count_prompt_telemetry:
        record_prompt_telemetry(config, prompt, is_direct_message=is_direct_message)
    reply_target = config["nick"] if target_name else None
    start_time = perf_counter()

    async for event in agent_or_team.run_stream(task=prompt):
        source = getattr(event, "source", None)
        content = coerce_message_content(getattr(event, "content", None))
        if not source or not content or source.lower() == "user":
            continue

        author = telemetry_name or (display_agent_name(source) if source in get_agent_specs() else source)
        telemetry_agent_name = author.replace("-", "_") if author == "GPT-5" else author
        usage = extract_usage_metrics(event)
        resolved_pricing = pricing
        if resolved_pricing is None and source in get_agent_specs():
            resolved_pricing = get_agent_specs()[source].get("pricing")
        latency_ms = round((perf_counter() - start_time) * 1000, 2)
        record_agent_response(
            config,
            telemetry_agent_name,
            prompt,
            content,
            latency_ms,
            pricing=resolved_pricing,
            usage=usage,
        )
        entry = add_history_entry(author=author, content=content, kind="message", target=reply_target)
        await cl.Message(author=author, content=render_entry(entry)).send()

    if count_prompt_telemetry and telemetry_name is None and target_name is None:
        await maybe_run_auto_bridge()



from chainlit.input_widget import Select, TextInput, Switch

async def update_settings_ui():
    agent_specs = get_agent_specs()
    config = get_config()

    widgets = [
        TextInput(
            id="topic",
            label="Room Topic",
            initial=config.get("topic", "")
        )
    ]

    for agent_name in agent_specs.keys():
        widgets.append(
            Switch(
                id=f"agent_{agent_name}",
                label=f"Enable {agent_name}",
                initial=agent_name in config["enabled_agents"]
            )
        )

    settings = await cl.ChatSettings(widgets).send()

@cl.on_settings_update
async def setup_agent(settings):
    config = get_config()
    agent_specs = get_agent_specs()
    changed = False

    if "topic" in settings and settings["topic"] != config["topic"]:
        config["topic"] = settings["topic"]
        await send_system_notice(f"Topic changed to: {config['topic']}")
        changed = True

    enabled_agents = []
    for agent_name in agent_specs.keys():
        key = f"agent_{agent_name}"
        if key in settings and settings[key]:
            enabled_agents.append(agent_name)

    if set(enabled_agents) != set(config["enabled_agents"]):
        config["enabled_agents"] = enabled_agents
        changed = True

    if changed:
        rebuild_team()
        await update_settings_ui()
        save_current_room_state()

@cl.on_chat_start
async def start():
    target_file = STATE_FILE
    persistent_state = load_persistent_state(target_file)
    cl.user_session.set(SESSION_STATE_KEY, persistent_state)

    import random
    def random_color():
        return "#" + "".join(random.choices("0123456789ABCDEF", k=6))

    # Initialize core free models from multiple providers
    default_models = [
        {"id": "openrouter/free", "base_url": None},
        {"id": "kilo-auto/free", "base_url": "https://api.kilo.ai/api"},
        {"id": "cline/free", "base_url": "https://api.cline.bot/api/v1"}
    ]
    
    current_specs = persistent_state.get("agent_specs", {})
    if not isinstance(current_specs, dict):
        current_specs = {}

    # Migration & Cleanup: Remove old/paid models and fix invalid IDs
    to_delete = []
    for name, spec in current_specs.items():
        m_id = spec.get("model", "")
        # Remove old hardcoded models
        if any(x in m_id.lower() for x in ["anthropic", "gpt-4", "gpt-5", "grok-2", "gemini-1.5-pro"]):
            to_delete.append(name)
            continue
        # Migrate invalid Kilo ID
        if m_id == "kilocode/free":
            spec["model"] = "kilo-auto/free"
            spec["base_url"] = "https://api.kilo.ai/api"
    
    for name in to_delete:
        del current_specs[name]

    # We always ensure the default models are present and have correct base_urls
    await send_system_notice("Identifying core free models from multiple providers...")
    for model_data in default_models:
        model_id = model_data["id"]
        b_url = model_data["base_url"]
        
        # Check if already identified in persistent state
        found_name = None
        for name, s in current_specs.items():
            if isinstance(s, dict) and s.get("model") == model_id:
                found_name = name
                # Ensure base_url is up to date even if previously saved
                s["base_url"] = b_url
                break
        
        if not found_name:
            nick = await identify_model_nick(model_id, base_url=b_url)
            # Ensure unique name
            base_nick = nick
            counter = 1
            while nick in current_specs:
                nick = f"{base_nick}{counter}"
                counter += 1
            
            current_specs[nick] = {
                "model": model_id,
                "base_url": b_url,
                "color": random_color(),
                "bio": f"Auto-routed free model from {model_id.split('/')[0]}.",
                "pricing": {"input_per_million": 0.0, "output_per_million": 0.0}
            }

    # Also fetch all available free models for selection from OpenRouter
    try:
        await send_system_notice("Fetching available free models from OpenRouter...")
        all_free = await fetch_free_models()
        for m in all_free:
            m_id = m["id"]
            already_in = False
            for name, s in current_specs.items():
                if isinstance(s, dict) and s.get("model") == m_id:
                    already_in = True
                    break
            
            if not already_in:
                name = re.sub(r"[^a-zA-Z0-9_]", "_", m["name"])
                if name in current_specs:
                    name = name + "_" + m_id.split("/")[-1].replace("-", "_").replace(":", "_").replace(".", "_")
                
                current_specs[name] = {
                    "model": m_id,
                    "color": random_color(),
                    "bio": m["description"][:200],
                    "pricing": {"input_per_million": 0.0, "output_per_million": 0.0}
                }
    except Exception as e:
        await send_system_notice(f"Warning: model fetch failed: {e}")

    update_agent_specs(current_specs)
    
    rooms = make_initial_rooms(current_specs, persistent_state)
    cl.user_session.set(SESSION_ROOMS_KEY, rooms)
    cl.user_session.set(SESSION_ROOM_KEY, DEFAULT_ROOM_NAME)
    
    # Update config
    config = rooms[DEFAULT_ROOM_NAME]["config"]
    
    # Clean up enabled_agents in config from deleted agents
    config["enabled_agents"] = [a for x in [config.get("enabled_agents", [])] for a in x if a in current_specs]

    # If this is a fresh start or missing core models, enable them
    core_names = []
    for name, s in current_specs.items():
        if s.get("model") in [dm["id"] for dm in default_models]:
            core_names.append(name)
    
    # If no agents enabled or core trio missing, fix it
    if not config.get("enabled_agents"):
        config["enabled_agents"] = core_names
    else:
        for cn in core_names:
            if cn not in config["enabled_agents"]:
                config["enabled_agents"].append(cn)
    
    cl.user_session.set(SESSION_CONFIG_KEY, config)
    cl.user_session.set(SESSION_HISTORY_KEY, rooms[DEFAULT_ROOM_NAME]["history"])
    cl.user_session.set(SESSION_AUTOMATION_TASK_KEY, None)
    cl.user_session.set(SESSION_REPLAY_STATE_KEY, None)
    
    rebuild_team()
    await update_settings_ui()

    version = "Unknown"
    if os.path.exists("VERSION"):
        with open("VERSION", "r") as vf:
            version = vf.read().strip()

    welcome_banner = f"""
*** Connected to #agentirc (AutoGen Network) [AgentIRC v{version}]
*** Current Room: {config['room_name']}
*** Your nick is {config['nick']}
*** Current Topic: {config['topic']}
*** Current Mode: {config['mode'].upper()}
*** Scenario: {config['scenario']}
*** Moderator: {config['moderator_mode']}
*** Enabled Agents: {', '.join(display_agent_name(name) for name in config['enabled_agents'])}
*** Type /help for commands.
"""
    await cl.Message(content=welcome_banner).send()
    log_irc(f"--- Session Started: {datetime.now()} ---")
    add_history_entry(author="system", content="Session started.", kind="system")


@cl.on_chat_end
async def end():
    await stop_automation_task()


@cl.on_message
async def handle_message(message: cl.Message):
    content = message.content.strip()
    images = []
    if message.elements:
        for element in message.elements:
            if "image" in element.mime:
                images.append(element)

    if not content and not images:
        await send_system_notice("Empty messages are ignored.")
        return

    config = get_config()

    if images:
        content += "\n[User attached images]"

    add_history_entry(author=config["nick"], content=content, kind="user")

    parsed_command = parse_command(content)
    if parsed_command:
        command, args = parsed_command
        try:
            await handle_command(command, args)
        except Exception as exc:
            record_error(config)
            await send_system_notice(f"Command failed: {exc}")
        return

    active_agents = list(config["enabled_agents"])
    target_name, body = parse_direct_message(content, active_agents)
    if content.startswith("@") and target_name is None:
        available = ", ".join(display_agent_name(name) for name in active_agents)
        await send_system_notice(f"Unknown or ambiguous DM target. Active agents: {available}")
        return

    prompt = body or f"Please respond to the current topic: {config['topic']}"

    images = []
    if getattr(message, "elements", None):
        from autogen_core import Image as AGImage
        for element in message.elements:
            if "image" in element.mime.lower():
                try:
                    img = AGImage.from_file(element.path)
                    images.append(img)
                except Exception as e:
                    await send_system_notice(f"Failed to load image: {e}")

    task_payload = [prompt]
    if images:
        task_payload.extend(images)

    # If it's just text, unwrap the list so standard tools work, else keep as list for multimodal
    if len(task_payload) == 1:
        task_payload = task_payload[0]

    try:
        if target_name:
            team = cl.user_session.get(SESSION_TEAM_KEY)
            target_agent = next((agent for agent in team.participants if agent.name == target_name), None)
            if target_agent is None:
                await send_system_notice(f"{display_agent_name(target_name)} is not available in the active lineup.")
                return
            await send_system_notice(f"Private message to {display_agent_name(target_name)}...")
            await stream_agent(target_agent, task_payload, target_name=display_agent_name(target_name))
            return

        team = cl.user_session.get(SESSION_TEAM_KEY)
        await stream_agent(team, task_payload)
    except Exception as exc:
        record_error(config)
        await send_system_notice(f"Simulation failed: {exc}")
