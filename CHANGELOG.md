# Changelog

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
- Expanded unit coverage from 17 to 20 tests.
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
