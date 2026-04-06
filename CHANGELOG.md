# Changelog

## 0.18.0 - 2026-04-05
- Added `/health` for compact room health scoring across the session.
- Added `tests/test_bridge_runtime.py` for bridge runtime outbox-processing behavior coverage.
- Updated build tooling to compile bridge runtime behavior tests.
- Expanded README, design, implementation, testing, changelog, and handoff documentation for room health and runtime behavior validation.
- Expanded test discovery coverage to 44 discovered tests with 2 opt-in live tests skipped by default.

## 0.17.0 - 2026-04-05
- Added `websocket_bridge_runtime.py` as a websocket transport scaffold for outbox payloads.
- Added `tests/test_websocket_bridge_runtime.py` for websocket runtime scaffold coverage.
- Added `websockets>=13.0` to `requirements.txt`.
- Updated build tooling to compile websocket runtime modules and tests.
- Expanded README, design, implementation, testing, changelog, and handoff documentation for websocket transport scaffolding.

## 0.16.0 - 2026-04-05
- Added `irc_bridge_runtime.py` as a standard-library IRC transport scaffold for outbox payloads.
- Added `tests/test_irc_bridge_runtime.py` for IRC payload formatting coverage.
- Added `tests/test_live_integration.py` as an opt-in live provider integration test gate.
- Updated build tooling to compile IRC runtime and live test modules.
- Expanded README, findings, design, implementation, testing, changelog, and handoff documentation for IRC/runtime scaffolding and live test strategy.
- Expanded unit/test discovery coverage to 42 discovered tests with 2 opt-in live tests skipped by default.

## 0.15.0 - 2026-04-05
- Added reusable saved auto-bridge policy presets with `/bridge-policies`, `/save-bridge-policy`, `/load-bridge-policy`, and `/delete-bridge-policy`.
- Added helper-layer persistence support for `saved_bridge_policies` in `data/simulator_state.json`.
- Expanded unit coverage from 35 to 36 tests.
- Expanded README, design, implementation, testing, findings, changelog, and handoff documentation for auto-bridge policy persistence.

## 0.14.0 - 2026-04-05
- Added `/auto-bridge`, `/auto-bridge stop`, and status rendering for prompt-interval bridge automation.
- Added room archive workflow with `/archives`, `/archive-room`, and `/restore-room`.
- Added `data/archives/` archive support in the core helper layer.
- Expanded runtime docs and operator docs for room persistence and auto-bridge behavior.
- Expanded unit coverage from 32 to 35 tests.

## 0.13.0 - 2026-04-05
- Added tool-use plugin support via `simulator_tools.py` with default memory/calc/time tools.
- Added tool-control commands: `/tools`, `/enable-tool <name>`, `/disable-tool <name>`.
- Added role-specific bridge agents via `/bridge-ai <source> <target> [role] [focus]`.
- Added `/bridge-roles` command to inspect available bridge agent specializations.
- Added `webhook` connector adapter in `bridge_connectors.py` with `--endpoint` URL support.
- Replaced bulleted observer and dashboard views with richer Markdown metrics tables.
- Included `simulator_tools.py` in compilation checks.
- Expanded unit coverage from 31 to 32 tests.
- Expanded README, findings, design, implementation, testing, changelog, and handoff documentation for tools and role-based bridge agents.

## 0.12.0 - 2026-04-05
- Added `/connectors` for connector adapter inspection.
- Added `bridge_connectors.py` with `console`, `inbox`, and `jsonl` connector adapters.
- Added connector-aware bridge runtime processing via `bridge_runtime.py --connector <name>`.
- Expanded inbox/runtime support with `/bridge-runtime`, `/inbox`, and `/import-bridge <file> [room]` command flow.
- Expanded build tooling to compile `bridge_connectors.py` and `tests/test_bridge_connectors.py`.
- Expanded unit coverage from 26 to 31 tests across the helper layer and connector adapter layer.
- Expanded README, findings, design, implementation, testing, changelog, and handoff documentation for connector adapters and staged external runtime evolution.

## 0.11.0 - 2026-04-05
- Added `/bridge-runtime` for external bridge directory status visibility.
- Added `/inbox` and `/import-bridge <file> [room]` for inbound external payload inspection and import.
- Added `bridge_runtime.py` as a standalone outbox-processing runtime scaffold.
- Added `inbox/` and `processed/` directory concepts alongside the existing `outbox/` foundation.
- Expanded telemetry with `external_imports` tracking.
- Expanded build tooling to compile `bridge_runtime.py`.
- Expanded unit coverage from 25 to 26 tests.
- Expanded README, findings, design, implementation, testing, changelog, and handoff documentation for inbox/runtime scaffolding.

## 0.10.0 - 2026-04-05
- Added `/bridge-export <room> [count]` for external room snapshot payload generation.
- Added `/outbox` for inspecting generated external bridge payload files.
- Added standardized external payload helpers for `room_snapshot` and `bridge_note` artifacts.
- Added `outbox/` as the external connector foundation directory.
- Expanded telemetry with `external_exports` tracking.
- Expanded dashboard, observer, telemetry, analytics, exports, README, findings, design, implementation, testing, changelog, and handoff documentation for external payload foundations.
- Expanded unit coverage from 24 to 25 tests.

## 0.9.0 - 2026-04-05
- Added `/observer` for ranked multi-room operational visibility.
- Added `/bridge-ai <source> <target> [focus]` for model-generated cross-room bridge notes.
- Expanded telemetry with `bridge_ai_events` and `observer_views`.
- Expanded analytics, telemetry, exports, and dashboard surfaces to account for observer and bridge-AI usage.
- Expanded unit coverage from 24 to 24 tests while increasing helper-layer assertions for observer and bridge-AI behavior.
- Expanded README, findings, design, implementation, testing, changelog, and handoff documentation for observer views and bridge-agent workflows.

## 0.8.0 - 2026-04-05
- Added `/room-analytics [name]` for room-specific analytics inspection.
- Added `/bridge <source> <target> [count]` for deterministic cross-room bridge-note delivery.
- Expanded `/dashboard` with aggregate prompt and bridge metrics across rooms.
- Expanded telemetry with bridge-event tracking.
- Expanded unit coverage from 23 to 24 tests.
- Expanded README, findings, design, implementation, testing, changelog, and handoff documentation for bridge notes and room analytics.

## 0.7.0 - 2026-04-05
- Added `/dashboard` and `/room-summary` for operator-level multi-room visibility.
- Added interactive replay stepping with `/replay-open` and `/replay-step` using session-scoped replay cursor state.
- Added replay-window helpers and dashboard/room-summary rendering helpers.
- Made README, design, implementation, testing, findings, changelog, and handoff documentation reflect dashboard and replay-step behavior.
- Maintained passing unit and compile validation (23 tests passing).

## 0.6.0 - 2026-04-05
- Added multi-room session support with `/rooms`, `/room`, `/new-room`, and `/delete-room`.
- Added room-local config/history management with room-aware reset and clear behavior.
- Made prompts, status, and welcome banner room-aware.
- Added room helpers for creation, switching, deletion, and listing.
- Expanded unit coverage from 22 to 23 tests.
- Expanded README, findings, design, implementation, testing, changelog, and handoff documentation for multi-room behavior.

## 0.5.0 - 2026-04-05
- Added hybrid cost tracking with `/costs`, configurable pricing hints, usage extraction helpers, and side-by-side estimated vs actual cost accounting.
- Added saved job presets with `/jobs`, `/save-job`, `/run-job`, and `/delete-job`.
- Added replay comparison with `/compare <left> <right> [count]` and support for `previous` replay resolution.
- Expanded telemetry with comparison counters, token totals, per-agent cost tracking, and usage sample counts.
- Expanded persistent state to include saved jobs.
- Expanded unit coverage from 20 to 22 tests.
- Expanded README, findings, design, implementation, testing, changelog, and handoff documentation for cost tracking, replay comparison, and saved jobs.

## 0.4.0 - 2026-04-05
- Added autonomous scheduling with `/schedule`, bounded run counts, schedule status, and schedule-stop support.
- Added replay support with `/replays`, `/replay`, export discovery helpers, and replay rendering from JSON transcript artifacts.
- Extended telemetry with scheduled-run and replay-view counters.
- Added autonomous prompt generation helpers and schedule status helpers.
- Added automation-task cleanup on chat end and reset.
- Expanded design, implementation, testing, README, findings, and handoff documentation for scheduling and replay behavior.

## 0.3.0 - 2026-04-05
- Added session telemetry for prompts, direct messages, judge runs, errors, per-agent message counts, estimated tokens, and average response latency.
- Added moderator modes (`off`, `facilitator`, `strict`, `critic`, `chaos`) and threaded them into agent system prompts.
- Added persistent persona overrides with `/personas` and `/persona` commands.
- Added persistent lineup management with `/lineups`, `/save-lineup`, `/load-lineup`, and `/delete-lineup`.
- Added `/telemetry`, `/analytics`, and `/judge` commands for operational visibility and transcript evaluation.
- Added `data/simulator_state.json` support for durable simulator operator state.
- Expanded scenarios with `product` and `council` presets.
- Added design documentation with a mermaid flow diagram.
- Expanded unit coverage from 10 to 17 tests.

## 0.2.0 - 2026-04-05
- Added `simulator_core.py` to centralize simulator state, command parsing, transcript formatting, scenario presets, and export helpers.
- Expanded the Chainlit app with `/status`, `/agents`, `/whois`, `/enable`, `/disable`, `/rounds`, `/scenario`, `/history`, `/export`, and `/reset` commands.
- Added support for dynamic agent-lineup control and configurable discuss-mode turn limits.
- Added transcript export to Markdown and JSON under `exports/`.
- Fixed agent name rendering so internal names like `GPT_5` display correctly as `GPT-5`.
- Added unit tests for the new simulation helper layer.
- Added AI DevKit implementation/testing documentation for this feature pass.
