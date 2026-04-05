import os
import asyncio
import typing
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

from simulator_core import (
    EXPORT_DIR,
    MODERATOR_MODES,
    STATE_FILE,
    apply_scenario,
    append_history,
    build_agent_detail_text,
    build_agents_text,
    build_analytics_text,
    build_autonomous_prompt,
    build_costs_text,
    build_help_text,
    build_history_text,
    build_jobs_text,
    build_judge_prompt,
    build_lineup_text,
    build_lineups_text,
    build_moderator_modes_text,
    build_personas_text,
    build_replay_comparison_text,
    build_replay_text,
    build_replays_text,
    build_schedule_status_text,
    build_scenarios_text,
    build_status_text,
    build_telemetry_text,
    coerce_message_content,
    configure_automation,
    delete_job,
    delete_lineup,
    display_agent_name,
    export_transcript,
    extract_usage_metrics,
    list_export_files,
    load_job,
    load_lineup,
    load_persistent_state,
    load_replay_payload,
    make_default_config,
    make_entry,
    parse_command,
    parse_direct_message,
    record_agent_response,
    record_comparison_view,
    record_error,
    record_judge_run,
    record_prompt_telemetry,
    record_replay_view,
    record_scheduled_run,
    render_entry,
    resolve_agent_name,
    resolve_replay_file,
    save_job,
    save_lineup,
    save_persistent_state,
    set_agent_enabled,
    set_moderator_mode,
    set_persona_override,
    set_rounds,
    stop_automation,
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
JUDGE_PRICING = {"input_per_million": 0.15, "output_per_million": 0.6}

AGENT_SPECS = {
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


def log_irc(message: str):
    with open(LOG_FILE, "a", encoding="utf-8") as handle:
        handle.write(f"{message}\n")



def get_client(model_name: str):
    return OpenAIChatCompletionClient(
        model=model_name,
        api_key=os.environ.get("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
        model_info={
            "vision": False,
            "function_calling": True,
            "json_output": True,
            "structured_output": True,
            "family": "unknown",
        },
    )



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
        cl.user_session.set(SESSION_STATE_KEY, state)
    return state



def persist_state():
    state = get_persistent_state()
    save_persistent_state(state, STATE_FILE)



def get_automation_task() -> asyncio.Task | None:
    return cl.user_session.get(SESSION_AUTOMATION_TASK_KEY)



def set_automation_task(task: asyncio.Task | None):
    cl.user_session.set(SESSION_AUTOMATION_TASK_KEY, task)


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

    for name in enabled_agents:
        spec = AGENT_SPECS[name]
        peers = [display_agent_name(peer) for peer in enabled_agents if peer != name]
        persona = config.get("persona_overrides", {}).get(name, spec["bio"])
        system_message = (
            f"You are {display_agent_name(name)} in an IRC-style multi-model simulation. "
            f"Mode: {config['mode'].upper()}. Scenario: {config['scenario']}. "
            f"Topic: {config['topic']}. Persona: {persona} "
            f"Peers: {', '.join(peers) if peers else 'none'}. "
            f"Moderator mode: {config['moderator_mode']} ({MODERATOR_MODES[config['moderator_mode']]}) "
            "Respond in plain text with a concise, useful IRC-style reply. "
            "Stay in character, avoid markdown headers, and keep it easy to scan."
        )

        if config["mode"] == "discuss":
            system_message += " Engage with peer ideas when helpful. Say TERMINATE only when the discussion is meaningfully complete."
        else:
            system_message += " Reply exactly once to each incoming prompt."

        agent = AssistantAgent(
            name=name,
            model_client=get_client(spec["model"]),
            system_message=system_message,
        )
        agents.append(agent)

    if config["mode"] == "broadcast":
        termination = MaxMessageTermination(len(agents) + 1)
        return RoundRobinGroupChat(agents, termination_condition=termination)

    termination = TextMentionTermination("TERMINATE") | MaxMessageTermination(config["max_rounds"])
    selector_client = get_client("openai/gpt-4o-mini")
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
        rebuild_team()
        await send_system_notice(f"Topic changed to: {args}")
        return True

    if command == "/nick":
        if not args:
            await send_system_notice(f"Current nick: {config['nick']}")
            return True
        config["nick"] = args
        await send_system_notice(f"Your nick is now **{args}**.")
        return True

    if command == "/status":
        await cl.Message(content=build_status_text(config, len(get_history()), persistent_state)).send()
        return True

    if command == "/lineup":
        await cl.Message(content=build_lineup_text(AGENT_SPECS, config["enabled_agents"])).send()
        return True

    if command == "/agents":
        await cl.Message(content=build_agents_text(AGENT_SPECS, config["enabled_agents"], config)).send()
        return True

    if command == "/whois":
        if not args:
            await send_system_notice("Usage: `/whois <agent>`")
            return True
        agent_name = resolve_agent_name(args, list(AGENT_SPECS.keys()))
        if not agent_name:
            await send_system_notice(f"Unknown agent: `{args}`")
            return True
        await cl.Message(content=build_agent_detail_text(agent_name, AGENT_SPECS, config["enabled_agents"], config)).send()
        return True

    if command in {"/enable", "/disable"}:
        if not args:
            await send_system_notice(f"Usage: `{command} <agent>`")
            return True
        changed, response = set_agent_enabled(
            config=config,
            raw_name=args,
            enabled=command == "/enable",
            agent_specs=AGENT_SPECS,
        )
        if changed:
            rebuild_team()
        await send_system_notice(response)
        return True

    if command == "/rounds":
        if not args:
            await send_system_notice(f"Current discuss-mode max rounds: {config['max_rounds']}")
            return True
        changed, response = set_rounds(config, args)
        if changed and config["mode"] == "discuss":
            rebuild_team()
        await send_system_notice(response)
        return True

    if command == "/scenario":
        if not args:
            await cl.Message(content=build_scenarios_text()).send()
            return True
        changed, response = apply_scenario(config, args, AGENT_SPECS)
        if changed:
            rebuild_team()
        await send_system_notice(response)
        return True

    if command == "/moderator":
        if not args:
            await cl.Message(content=build_moderator_modes_text()).send()
            return True
        changed, response = set_moderator_mode(config, args)
        if changed:
            rebuild_team()
        await send_system_notice(response)
        return True

    if command == "/telemetry":
        await cl.Message(content=build_telemetry_text(config, AGENT_SPECS)).send()
        return True

    if command == "/analytics":
        await cl.Message(content=build_analytics_text(config, get_history(), AGENT_SPECS)).send()
        return True

    if command == "/costs":
        await cl.Message(content=build_costs_text(config, AGENT_SPECS)).send()
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
        await cl.Message(content=build_personas_text(config, AGENT_SPECS)).send()
        return True

    if command == "/persona":
        if not args:
            await send_system_notice("Usage: `/persona <agent> <text>` or `/persona clear <agent>`")
            return True

        if args.lower().startswith("clear "):
            clear_target = args.split(" ", 1)[1].strip()
            changed, response = set_persona_override(config, persistent_state, clear_target, "", AGENT_SPECS)
        else:
            parts = args.split(" ", 1)
            if len(parts) < 2:
                await send_system_notice("Usage: `/persona <agent> <text>` or `/persona clear <agent>`")
                return True
            changed, response = set_persona_override(config, persistent_state, parts[0], parts[1], AGENT_SPECS)

        if changed:
            persist_state()
            rebuild_team()
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
        changed, response = load_lineup(config, persistent_state, args, AGENT_SPECS)
        if changed:
            rebuild_team()
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
        changed, response = load_job(config, persistent_state, args, AGENT_SPECS)
        if changed:
            rebuild_team()
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
        await send_system_notice("Transcript buffer cleared for this session.")
        return True

    if command == "/reset":
        await stop_automation_task()
        cl.user_session.set(SESSION_CONFIG_KEY, make_default_config(AGENT_SPECS, persistent_state))
        save_history([])
        rebuild_team()
        await send_system_notice("Simulator state reset to defaults.")
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

        author = telemetry_name or (display_agent_name(source) if source in AGENT_SPECS else source)
        telemetry_agent_name = author.replace("-", "_") if author == "GPT-5" else author
        usage = extract_usage_metrics(event)
        resolved_pricing = pricing
        if resolved_pricing is None and source in AGENT_SPECS:
            resolved_pricing = AGENT_SPECS[source].get("pricing")
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


@cl.on_chat_start
async def start():
    persistent_state = load_persistent_state(STATE_FILE)
    cl.user_session.set(SESSION_STATE_KEY, persistent_state)
    config = make_default_config(AGENT_SPECS, persistent_state)
    cl.user_session.set(SESSION_CONFIG_KEY, config)
    cl.user_session.set(SESSION_HISTORY_KEY, [])
    cl.user_session.set(SESSION_AUTOMATION_TASK_KEY, None)
    rebuild_team()

    welcome_banner = f"""
```
*** Connected to #agentirc (AutoGen Network)
*** Your nick is {config['nick']}
*** Current Topic: {config['topic']}
*** Current Mode: {config['mode'].upper()}
*** Scenario: {config['scenario']}
*** Moderator: {config['moderator_mode']}
*** Enabled Agents: {', '.join(display_agent_name(name) for name in config['enabled_agents'])}
*** Type /help for commands.
```
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
    if not content:
        await send_system_notice("Empty messages are ignored.")
        return

    config = get_config()
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

    try:
        if target_name:
            team = cl.user_session.get(SESSION_TEAM_KEY)
            target_agent = next((agent for agent in team.participants if agent.name == target_name), None)
            if target_agent is None:
                await send_system_notice(f"{display_agent_name(target_name)} is not available in the active lineup.")
                return
            await send_system_notice(f"Private message to {display_agent_name(target_name)}...")
            await stream_agent(target_agent, prompt, target_name=display_agent_name(target_name))
            return

        team = cl.user_session.get(SESSION_TEAM_KEY)
        await stream_agent(team, prompt)
    except Exception as exc:
        record_error(config)
        await send_system_notice(f"Simulation failed: {exc}")
