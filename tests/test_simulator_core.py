import json
import os
import tempfile
import unittest
from pathlib import Path

from simulator_core import (
    MODERATOR_MODES,
    STATE_FILE,
    apply_scenario,
    append_history,
    build_analytics_text,
    build_judge_prompt,
    build_lineups_text,
    build_moderator_modes_text,
    build_personas_text,
    build_status_text,
    build_telemetry_text,
    delete_lineup,
    display_agent_name,
    export_transcript,
    load_lineup,
    load_persistent_state,
    make_default_config,
    make_default_store,
    make_entry,
    parse_command,
    parse_direct_message,
    record_agent_response,
    record_judge_run,
    record_prompt_telemetry,
    render_entry,
    resolve_agent_name,
    save_lineup,
    save_persistent_state,
    set_agent_enabled,
    set_moderator_mode,
    set_persona_override,
    set_rounds,
)


AGENT_SPECS = {
    "Claude": {"model": "anthropic/claude-sonnet-4.6", "bio": "Nuanced and detailed."},
    "GPT_5": {"model": "openai/gpt-5.3-chat", "bio": "Logical and concise."},
    "Gemini": {"model": "google/gemini-3.1-flash-image-preview", "bio": "Creative and fact-driven."},
}


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

    def test_set_rounds_validates_range(self):
        config = make_default_config(AGENT_SPECS)
        changed, message = set_rounds(config, "12")
        self.assertTrue(changed)
        self.assertEqual(config["max_rounds"], 12)
        changed, message = set_rounds(config, "99")
        self.assertFalse(changed)
        self.assertIn("between 2 and 30", message)

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

    def test_prompt_and_response_telemetry(self):
        config = make_default_config(AGENT_SPECS)
        record_prompt_telemetry(config, "hello models", is_direct_message=False)
        record_prompt_telemetry(config, "hello claude", is_direct_message=True)
        record_judge_run(config)
        record_agent_response(config, "Claude", "hello there", 120.5)
        record_agent_response(config, "Judge", "winner: Claude", 220.0)
        telemetry_text = build_telemetry_text(config, AGENT_SPECS)
        analytics_text = build_analytics_text(config, [], AGENT_SPECS)
        self.assertIn("Prompts sent: `2`", telemetry_text)
        self.assertIn("Judge", telemetry_text)
        self.assertIn("Most talkative agent", analytics_text)

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
            save_persistent_state(state, path)
            loaded = load_persistent_state(path)
            self.assertEqual(loaded["saved_personas"]["Claude"], "Test persona")

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

    def test_display_agent_name(self):
        self.assertEqual(display_agent_name("GPT_5"), "GPT-5")
        self.assertEqual(display_agent_name("Gemini"), "Gemini")

    def test_default_moderator_modes_exist(self):
        self.assertIn("off", MODERATOR_MODES)
        self.assertIn("critic", MODERATOR_MODES)


if __name__ == "__main__":
    unittest.main()
