import json
import os
import tempfile
import unittest
from pathlib import Path

from simulator_core import (
    DEFAULT_ROOM_NAME,
    EXPORT_DIR,
    INBOX_DIR,
    MODERATOR_MODES,
    STATE_FILE,
    apply_scenario,
    append_history,
    build_analytics_text,
    build_archives_text,
    build_auto_bridge_status_text,
    build_autonomous_prompt,
    OUTBOX_DIR,
    build_bridge_note,
    build_bridge_prompt,
    build_costs_text,
    build_dashboard_text,
    build_jobs_text,
    build_judge_prompt,
    build_lineups_text,
    build_bridge_runtime_status_text,
    build_external_bridge_payload,
    build_external_room_payload,
    build_imported_payload_text,
    build_inbox_text,
    build_observer_text,
    build_moderator_modes_text,
    build_personas_text,
    build_replay_comparison_text,
    build_replay_text,
    build_replay_window_text,
    build_replays_text,
    build_room_analytics_text,
    build_room_summary_text,
    build_rooms_text,
    build_schedule_status_text,
    build_status_text,
    build_telemetry_text,
    calculate_cost_usd,
    configure_auto_bridge,
    configure_automation,
    create_room,
    delete_job,
    delete_lineup,
    delete_room,
    display_agent_name,
    estimate_tokens,
    export_transcript,
    extract_usage_metrics,
    list_export_files,
    list_inbox_files,
    list_outbox_files,
    list_room_archives,
    load_external_payload,
    load_job,
    load_room_archive,
    load_lineup,
    load_persistent_state,
    make_initial_rooms,
    load_replay_payload,
    make_default_config,
    make_default_store,
    make_entry,
    normalize_usage_payload,
    parse_command,
    parse_direct_message,
    record_agent_response,
    record_bridge_ai_event,
    record_bridge_event,
    record_comparison_view,
    record_judge_run,
    record_observer_view,
    record_prompt_telemetry,
    record_replay_view,
    record_scheduled_run,
    render_entry,
    resolve_agent_name,
    resolve_replay_file,
    resolve_replay_window,
    save_job,
    save_lineup,
    save_persistent_state,
    save_room_archive,
    write_outbox_payload,
    set_agent_enabled,
    set_moderator_mode,
    switch_room,
    set_persona_override,
    set_rounds,
    set_tool_enabled,
    stop_auto_bridge,
    stop_automation,
)


AGENT_SPECS = {
    "Claude": {
        "model": "anthropic/claude-sonnet-4.6",
        "bio": "Nuanced and detailed.",
        "pricing": {"input_per_million": 3.0, "output_per_million": 15.0},
    },
    "GPT_5": {
        "model": "openai/gpt-5.3-chat",
        "bio": "Logical and concise.",
        "pricing": {"input_per_million": 1.25, "output_per_million": 10.0},
    },
    "Gemini": {
        "model": "google/gemini-3.1-flash-image-preview",
        "bio": "Creative and fact-driven.",
        "pricing": {"input_per_million": 0.35, "output_per_million": 1.05},
    },
}


class UsageStub:
    def __init__(self, prompt_tokens, completion_tokens):
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens


class EventStub:
    def __init__(self, usage=None):
        self.usage = usage


class SimulatorCoreTests(unittest.TestCase):
    def test_parse_command(self):
        self.assertEqual(parse_command("/mode discuss"), ("/mode", "discuss"))
        self.assertIsNone(parse_command("hello world"))

    def test_resolve_agent_name_accepts_display_aliases(self):
        self.assertEqual(resolve_agent_name("gpt-5", list(AGENT_SPECS.keys())), "GPT_5")
        self.assertEqual(resolve_agent_name("cla", list(AGENT_SPECS.keys())), "Claude")
        self.assertIsNone(resolve_agent_name("unknown", list(AGENT_SPECS.keys())))

    def test_parse_direct_message(self):
        agent_name, body = parse_direct_message("@gpt-5 summarize this", list(AGENT_SPECS.keys()))
        self.assertEqual(agent_name, "GPT_5")
        self.assertEqual(body, "summarize this")

    def test_set_agent_enabled_preserves_at_least_one_agent(self):
        config = make_default_config(AGENT_SPECS)
        changed, _ = set_agent_enabled(config, "gemini", enabled=False, agent_specs=AGENT_SPECS)
        self.assertTrue(changed)
        changed, _ = set_agent_enabled(config, "gpt-5", enabled=False, agent_specs=AGENT_SPECS)
        self.assertTrue(changed)
        changed, message = set_agent_enabled(config, "claude", enabled=False, agent_specs=AGENT_SPECS)
        self.assertFalse(changed)
        self.assertIn("At least one agent", message)

    def test_set_tool_enabled(self):
        config = make_default_config(AGENT_SPECS)
        self.assertEqual(config.get("enabled_tools", []), [])
        changed, message = set_tool_enabled(config, "get_current_time", True)
        self.assertTrue(changed)
        self.assertIn("get_current_time", config["enabled_tools"])
        changed, message = set_tool_enabled(config, "get_current_time", True)
        self.assertFalse(changed)
        self.assertIn("already enabled", message)
        changed, message = set_tool_enabled(config, "get_current_time", False)
        self.assertTrue(changed)
        self.assertNotIn("get_current_time", config["enabled_tools"])
        changed, message = set_tool_enabled(config, "unknown_tool", True)
        self.assertFalse(changed)
        self.assertIn("Unknown tool", message)

    def test_set_rounds_validates_range(self):
        config = make_default_config(AGENT_SPECS)
        changed, message = set_rounds(config, "12")
        self.assertTrue(changed)
        self.assertEqual(config["max_rounds"], 12)
        changed, message = set_rounds(config, "99")
        self.assertFalse(changed)
        self.assertIn("between 2 and 30", message)

    def test_auto_bridge_configuration_and_stop(self):
        config = make_default_config(AGENT_SPECS)
        changed, message = configure_auto_bridge(config, "war-room", "3", "ai", "technical", "focus")
        self.assertTrue(changed)
        self.assertIn("Auto-bridge enabled", message)
        status = build_auto_bridge_status_text(config)
        self.assertIn("war-room", status)
        self.assertIn("technical", status)
        stop_message = stop_auto_bridge(config)
        self.assertIn("stopped", stop_message.lower())

    def test_room_archive_save_load_and_list(self):
        persistent_state = make_default_store()
        rooms = make_initial_rooms(AGENT_SPECS, persistent_state)
        rooms[DEFAULT_ROOM_NAME]["history"].append(make_entry("Claude", "archived hello"))
        with tempfile.TemporaryDirectory() as temp_dir:
            archive_dir = Path(temp_dir)
            path = save_room_archive(DEFAULT_ROOM_NAME, rooms[DEFAULT_ROOM_NAME], archive_dir)
            self.assertTrue(path.exists())
            payload = load_room_archive(path)
            self.assertEqual(payload["room_name"], DEFAULT_ROOM_NAME)
            listed = list_room_archives(archive_dir)
            self.assertEqual(len(listed), 1)
            self.assertIn(path.name, build_archives_text(listed))

    def test_set_moderator_mode(self):
        config = make_default_config(AGENT_SPECS)
        changed, message = set_moderator_mode(config, "critic")
        self.assertTrue(changed)
        self.assertEqual(config["moderator_mode"], "critic")
        self.assertIn("critic", message)
        self.assertIn("chaos", build_moderator_modes_text())

    def test_apply_scenario_updates_configuration(self):
        config = make_default_config(AGENT_SPECS)
        changed, message = apply_scenario(config, "debate", AGENT_SPECS)
        self.assertTrue(changed)
        self.assertEqual(config["mode"], "discuss")
        self.assertEqual(config["scenario"], "debate")
        self.assertIn("Applied scenario", message)

    def test_history_rendering(self):
        history = []
        entry = append_history(history, make_entry("Claude", "hello there"))
        self.assertEqual(render_entry(entry).count("<Claude>"), 1)
        system_entry = append_history(history, make_entry("system", "ready", kind="system"))
        self.assertIn("*** ready", render_entry(system_entry))

    def test_status_text_contains_new_controls(self):
        config = make_default_config(AGENT_SPECS)
        config["simulation_count"] = 3
        persistent_state = make_default_store()
        status = build_status_text(config, history_size=5, persistent_state=persistent_state)
        self.assertIn("Claude", status)
        self.assertIn("judge model", status.lower())
        self.assertIn("Saved jobs", status)
        self.assertIn("Scheduled automation", status)
        self.assertIn("`3`", status)

    def test_persona_override_updates_config_and_persistent_state(self):
        config = make_default_config(AGENT_SPECS)
        persistent_state = make_default_store()
        changed, message = set_persona_override(
            config,
            persistent_state,
            "claude",
            "Architectural, opinionated, and blunt.",
            AGENT_SPECS,
        )
        self.assertTrue(changed)
        self.assertIn("Updated persona", message)
        self.assertIn("Architectural", build_personas_text(config, AGENT_SPECS))
        changed, message = set_persona_override(config, persistent_state, "claude", "", AGENT_SPECS)
        self.assertTrue(changed)
        self.assertIn("Cleared custom persona", message)

    def test_lineup_save_load_delete_cycle(self):
        config = make_default_config(AGENT_SPECS)
        persistent_state = make_default_store()
        config["enabled_agents"] = ["Claude", "GPT_5"]
        config["moderator_mode"] = "strict"
        changed, message = save_lineup(config, persistent_state, "Night Shift")
        self.assertTrue(changed)
        self.assertIn("night-shift", message)
        config["enabled_agents"] = ["Gemini"]
        changed, message = load_lineup(config, persistent_state, "night-shift", AGENT_SPECS)
        self.assertTrue(changed)
        self.assertEqual(config["enabled_agents"], ["Claude", "GPT_5"])
        self.assertIn("night-shift", build_lineups_text(persistent_state))
        changed, message = delete_lineup(persistent_state, "night-shift")
        self.assertTrue(changed)
        self.assertIn("Deleted lineup", message)

    def test_job_save_load_delete_cycle(self):
        config = make_default_config(AGENT_SPECS)
        persistent_state = make_default_store()
        config["enabled_agents"] = ["Claude", "Gemini"]
        configure_automation(config, "45", "3")
        changed, message = save_job(config, persistent_state, "nightly review")
        self.assertTrue(changed)
        self.assertIn("nightly-review", message)
        self.assertIn("nightly-review", build_jobs_text(persistent_state))
        config["enabled_agents"] = ["GPT_5"]
        changed, message = load_job(config, persistent_state, "nightly-review", AGENT_SPECS)
        self.assertTrue(changed)
        self.assertEqual(config["enabled_agents"], ["Claude", "Gemini"])
        self.assertEqual(config["automation"]["run_limit"], 3)
        changed, message = delete_job(persistent_state, "nightly-review")
        self.assertTrue(changed)
        self.assertIn("Deleted job", message)

    def test_room_create_switch_delete_cycle(self):
        persistent_state = make_default_store()
        rooms = make_initial_rooms(AGENT_SPECS, persistent_state)
        self.assertIn(DEFAULT_ROOM_NAME, rooms)
        changed, message, room_name = create_room(rooms, "War Room", AGENT_SPECS, persistent_state)
        self.assertTrue(changed)
        self.assertEqual(room_name, "war-room")
        self.assertIn("war-room", build_rooms_text(rooms, DEFAULT_ROOM_NAME))
        self.assertIn("Operator Dashboard", build_dashboard_text(rooms, DEFAULT_ROOM_NAME, persistent_state))
        self.assertIn("Room Summary", build_room_summary_text(rooms, 2))
        changed, message, room_name = switch_room(rooms, "war-room")
        self.assertTrue(changed)
        self.assertEqual(room_name, "war-room")
        changed, message, next_room = delete_room(rooms, "war-room", "war-room")
        self.assertTrue(changed)
        self.assertEqual(next_room, DEFAULT_ROOM_NAME)
        self.assertNotIn("war-room", rooms)

    def test_prompt_and_response_telemetry(self):
        config = make_default_config(AGENT_SPECS)
        record_prompt_telemetry(config, "hello models", is_direct_message=False)
        record_prompt_telemetry(config, "hello claude", is_direct_message=True)
        record_judge_run(config, "judge this transcript")
        record_scheduled_run(config, "scheduled autonomous prompt")
        record_replay_view(config)
        record_comparison_view(config)
        record_bridge_event(config)
        record_bridge_ai_event(config, "bridge prompt")
        record_observer_view(config)
        record_agent_response(
            config,
            "Claude",
            "hello models",
            "hello there",
            120.5,
            pricing=AGENT_SPECS["Claude"]["pricing"],
            usage={"prompt_tokens": 10, "completion_tokens": 20},
        )
        record_agent_response(
            config,
            "Judge",
            "judge this transcript",
            "winner: Claude",
            220.0,
            pricing={"input_per_million": 0.15, "output_per_million": 0.6},
        )
        telemetry_text = build_telemetry_text(config, AGENT_SPECS)
        analytics_text = build_analytics_text(config, [], AGENT_SPECS)
        costs_text = build_costs_text(config, AGENT_SPECS)
        self.assertIn("Prompts sent: `5`", telemetry_text)
        self.assertIn("Scheduled runs: `1`", telemetry_text)
        self.assertIn("Replay views: `1`", telemetry_text)
        self.assertIn("Comparisons: `1`", telemetry_text)
        self.assertIn("Bridge events: `1`", telemetry_text)
        self.assertIn("Bridge AI events: `1`", telemetry_text)
        self.assertIn("Observer views: `1`", telemetry_text)
        self.assertIn("Judge", telemetry_text)
        self.assertIn("Most talkative agent", analytics_text)
        self.assertIn("Bridge events: `1`", analytics_text)
        self.assertIn("Bridge AI events: `1`", analytics_text)
        self.assertIn("Observer views: `1`", analytics_text)
        self.assertIn("Total estimated cost", costs_text)
        self.assertIn("usage samples `1`", costs_text)

    def test_schedule_configuration_and_stop(self):
        config = make_default_config(AGENT_SPECS)
        changed, message = configure_automation(config, "30", "4")
        self.assertTrue(changed)
        self.assertIn("Scheduled **4**", message)
        self.assertTrue(config["automation"]["enabled"])
        self.assertIn("Interval seconds", build_schedule_status_text(config))
        stop_message = stop_automation(config)
        self.assertIn("stopped", stop_message.lower())
        self.assertFalse(config["automation"]["enabled"])

    def test_autonomous_prompt_contains_scenario(self):
        config = make_default_config(AGENT_SPECS)
        prompt = build_autonomous_prompt(config)
        self.assertIn("Autonomous simulation run #1", prompt)
        self.assertIn(config["scenario"], prompt)

    def test_room_analytics_and_bridge_note(self):
        persistent_state = make_default_store()
        rooms = make_initial_rooms(AGENT_SPECS, persistent_state)
        rooms[DEFAULT_ROOM_NAME]["history"].append(make_entry("Claude", "hello lobby"))
        create_room(rooms, "war room", AGENT_SPECS, persistent_state)
        analytics_text = build_room_analytics_text(DEFAULT_ROOM_NAME, rooms[DEFAULT_ROOM_NAME], AGENT_SPECS)
        observer_text = build_observer_text(rooms, DEFAULT_ROOM_NAME)
        bridge_note = build_bridge_note(DEFAULT_ROOM_NAME, "war-room", rooms[DEFAULT_ROOM_NAME], 1)
        bridge_prompt = build_bridge_prompt(DEFAULT_ROOM_NAME, "war-room", rooms[DEFAULT_ROOM_NAME], "risks", 1)
        room_payload = build_external_room_payload(DEFAULT_ROOM_NAME, rooms[DEFAULT_ROOM_NAME], 1)
        bridge_payload = build_external_bridge_payload(DEFAULT_ROOM_NAME, "war-room", bridge_note, rooms[DEFAULT_ROOM_NAME])
        self.assertIn("Room Analytics", analytics_text)
        self.assertIn("Observer View", observer_text)
        self.assertIn("Bridge from room", bridge_note)
        self.assertIn("hello lobby", bridge_note)
        self.assertIn("Source room", bridge_prompt)
        self.assertEqual(room_payload["kind"], "room_snapshot")
        self.assertEqual(bridge_payload["kind"], "bridge_note")

    def test_outbox_payload_writing_and_listing(self):
        persistent_state = make_default_store()
        rooms = make_initial_rooms(AGENT_SPECS, persistent_state)
        rooms[DEFAULT_ROOM_NAME]["history"].append(make_entry("Claude", "hello lobby"))
        payload = build_external_room_payload(DEFAULT_ROOM_NAME, rooms[DEFAULT_ROOM_NAME], 1)

        with tempfile.TemporaryDirectory() as temp_dir:
            outbox_dir = Path(temp_dir) / OUTBOX_DIR
            path = write_outbox_payload(payload, outbox_dir)
            self.assertTrue(path.exists())
            listed = list_outbox_files(outbox_dir)
            self.assertEqual(len(listed), 1)
            self.assertEqual(listed[0].name, path.name)

    def test_inbox_listing_runtime_status_and_imported_payload_text(self):
        persistent_state = make_default_store()
        rooms = make_initial_rooms(AGENT_SPECS, persistent_state)
        rooms[DEFAULT_ROOM_NAME]["history"].append(make_entry("Claude", "hello lobby"))
        payload = build_external_room_payload(DEFAULT_ROOM_NAME, rooms[DEFAULT_ROOM_NAME], 1)

        with tempfile.TemporaryDirectory() as temp_dir:
            inbox_dir = Path(temp_dir) / INBOX_DIR
            path = write_outbox_payload(payload, inbox_dir)
            listed = list_inbox_files(inbox_dir)
            self.assertEqual(len(listed), 1)
            self.assertIn(path.name, build_inbox_text(listed))
            loaded = load_external_payload(path)
            imported_text = build_imported_payload_text(loaded)
            self.assertIn("Imported room snapshot", imported_text)
            status_text = build_bridge_runtime_status_text()
            self.assertIn("Bridge Runtime Status", status_text)

    def test_usage_parsing_and_cost_calculation(self):
        normalized = normalize_usage_payload({"input_tokens": 11, "output_tokens": 7})
        self.assertEqual(normalized["prompt_tokens"], 11)
        self.assertEqual(normalized["completion_tokens"], 7)
        extracted = extract_usage_metrics(EventStub(UsageStub(9, 4)))
        self.assertEqual(extracted["prompt_tokens"], 9)
        self.assertEqual(extracted["completion_tokens"], 4)
        self.assertGreater(calculate_cost_usd(1000, 500, AGENT_SPECS["Claude"]["pricing"]), 0)
        self.assertGreater(estimate_tokens("hello world"), 0)

    def test_judge_prompt_contains_focus_and_transcript(self):
        config = make_default_config(AGENT_SPECS)
        history = [make_entry("Claude", "A thoughtful reply")]
        prompt = build_judge_prompt(history, config, "best architecture")
        self.assertIn("best architecture", prompt)
        self.assertIn("Claude", prompt)

    def test_persistent_state_round_trip(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / STATE_FILE
            state = make_default_store()
            state["saved_personas"]["Claude"] = "Test persona"
            state["saved_jobs"]["nightly-review"] = {"interval_seconds": 30, "run_limit": 2}
            save_persistent_state(state, path)
            loaded = load_persistent_state(path)
            self.assertEqual(loaded["saved_personas"]["Claude"], "Test persona")
            self.assertIn("nightly-review", loaded["saved_jobs"])

    def test_export_transcript_writes_markdown_and_json(self):
        config = make_default_config(AGENT_SPECS)
        history = [make_entry("Claude", "hello there")]

        with tempfile.TemporaryDirectory() as temp_dir:
            current_dir = Path.cwd()
            try:
                os.chdir(temp_dir)
                paths = export_transcript(history, config, "both")
                self.assertEqual(len(paths), 2)
                for raw_path in paths:
                    path = Path(raw_path)
                    self.assertTrue(path.exists())
                json_path = next(Path(path) for path in paths if path.endswith(".json"))
                payload = json.loads(json_path.read_text(encoding="utf-8"))
                self.assertEqual(payload["history"][0]["author"], "Claude")
            finally:
                os.chdir(current_dir)

    def test_replay_listing_loading_and_rendering(self):
        config = make_default_config(AGENT_SPECS)
        history = [make_entry("Claude", "hello there"), make_entry("Gemini", "I agree")]

        with tempfile.TemporaryDirectory() as temp_dir:
            current_dir = Path.cwd()
            try:
                os.chdir(temp_dir)
                export_transcript(history, config, "json")
                export_transcript(history, config, "json")
                exports = list_export_files(EXPORT_DIR)
                self.assertEqual(len(exports), 2)
                self.assertIn("agentirc-", build_replays_text(exports))
                resolved = resolve_replay_file("latest", EXPORT_DIR)
                previous = resolve_replay_file("previous", EXPORT_DIR)
                self.assertIsNotNone(resolved)
                self.assertIsNotNone(previous)
                payload = load_replay_payload(resolved)
                replay_text = build_replay_text(payload, resolved.name, 2)
                self.assertIn("Replay Window", replay_text)
                self.assertIn("Claude", replay_text)
                start, end = resolve_replay_window(len(payload["history"]), 0, 1)
                self.assertEqual((start, end), (0, 1))
                window_text = build_replay_window_text(payload, resolved.name, 1, 1)
                self.assertIn("Window:", window_text)
                comparison_text = build_replay_comparison_text(payload, resolved.name, payload, previous.name, 2)
                self.assertIn("Replay Comparison", comparison_text)
            finally:
                os.chdir(current_dir)

    def test_display_agent_name(self):
        self.assertEqual(display_agent_name("GPT_5"), "GPT-5")
        self.assertEqual(display_agent_name("Gemini"), "Gemini")

    def test_default_moderator_modes_exist(self):
        self.assertIn("off", MODERATOR_MODES)
        self.assertIn("critic", MODERATOR_MODES)


if __name__ == "__main__":
    unittest.main()
