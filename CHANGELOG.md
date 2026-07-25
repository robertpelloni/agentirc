## 0.46.0 - 2026-07-01
- Added `/bridge-websocket <ws_uri>` command for full multi-room real-time websocket bridging UI.
- Enhanced UI feedback for tool calls in the retro aesthetic.
- Added a fully headless mode driven entirely by IRC clients (`headless_irc.py`).
- Added Discord bot bridging (`discord_bridge.py`).
- Added GitHub PR review agent scaffold (`pr_review_agents.py`).
- Added MUD roleplay exploration mechanics via the `/go` command.
- Integrated authentic 1990s terminal CRT shader CSS.

## 0.41.0 - 2026-06-18
- Refined external bridge payloads for MCP compliance by adding an `mcp` connector adapter that formats outbound requests as strict JSON-RPC 2.0 messages.

## 0.40.0 - 2026-06-18
- Implemented advanced agent autonomous scheduling with persistent memory, allowing automation loops to survive server reboots.

## 0.39.0 - 2026-06-18
- Finalized SQLite database migration by deprecating `agents_config.json` and removing legacy flat JSON fallback routines, mitigating multi-tab concurrency issues.

## 0.38.0 - 2026-06-18
- Implemented typing indicators during multi-agent broadcasts via Chainlit's `cl.Step`.

## 0.37.0 - 2026-06-18
- Implemented custom frontend audio engine in `public/irc.js` to play classic terminal `beep.wav` silently on incoming agent messages without rendering visual audio blocks.

## 0.36.0 - 2026-06-18
- Implemented native local LLM support via Ollama. Models prefixed with `ollama/` route automatically to `localhost:11434`.

## 0.35.0 - 2026-06-18
- Implemented true native MCP server support exposing the simulator tool catalog via FastMCP.

## 0.34.0 - 2026-06-18
- Added comprehensive tests for vision processing covering Chainlit image element extraction and AutoGen PIL Image wrapping.

## 0.33.0 - 2026-06-18
- Implemented a dedicated Admin UI for tool management directly within the Chainlit `ChatSettings` interface, allowing users to interactively toggle `TOOL_CATALOG` features.

## 0.32.0 - 2026-06-18
- Refactored `fetch_webpage` and `web_search` in `simulator_tools.py` to correctly use `httpx.AsyncClient` resolving duplicate definitions.
- Completed comprehensive project state analysis, updating documentation in accordance with strict continuous execution protocols.

## 0.31.0 - 2026-05-19
- Added comprehensive integration tests for the `/add-model` command (`tests/test_add_model.py`) to verify it correctly updates state, modifies active team configurations, and saves to persistence correctly.
- Created `VERSION.md` as the single source of truth for the project version.

## 0.30.0 - 2026-04-17
- Executed the `Operator Polling` feature.
- Added a `/poll "Question?" Opt1 Opt2` command to `app.py` that formats a markdown voting UI and streams it directly into the active AI model context, forcing them to vote on the topic.

## 0.29.0 - 2026-04-17
- Executed the `MMORPG Mechanics` product pivot outlined in `IDEAS.md`.
- Added a `/go <room>` command to `app.py` that automatically triggers the `mud_exploration` scenario mode, forcing active agents into roleplaying as environmental NPCs in a text-based MUD adventure.

## 0.28.0 - 2026-04-17
- Executed the `GitHub PR Review Agents` product pivot outlined in `IDEAS.md`.
- Added `fetch_github_pr` async tool utilizing `httpx` to grab raw `.diff` patches directly from PR URLs and safely truncate them for LLM context ingestion.
- Updated `agents_config.json` with dedicated `Security_Auditor` and `Code_Critic` developer personas.
- Added `pr_review` scenario preset to `simulator_core.py` to automatically orchestrate Code Reviews.

## 0.27.0 - 2026-04-17
- Implemented the `discord` outbox bridge connector in `bridge_connectors.py` to seamlessly POST simulator chat payloads directly to a live Discord Webhook URL `--endpoint`.
- Automatically translates `room_snapshot` and `bridge_note` internal dictionaries into Discord's expected markdown strings, capping to 2000 characters to prevent API rejection.

## 0.26.1 - 2026-04-17
- Verified named transcript replay resolution works cleanly inside `simulator_core.py` without requiring a separate `replay.py` wrapper, satisfying the original README spec. Added a unit test validating explicit named filename lookups.

## 0.26.0 - 2026-04-17
- Implemented Active `Typing Indicators` inside `app.py::stream_agent`. The frontend now natively hooks `cl.Step` elements to dynamically report which individual AI model is *currently formulating a response* during massive multi-agent round-robin broadcasts.

## 0.25.0 - 2026-04-17
- Implemented `Authentic Terminal CRT Shader` inside `public/style.css` to add screen curvature, scanlines, and phosphor flickering, deeply enriching the 1990s IRC aesthetic requested in the original project specs.

## 0.24.0 - 2026-04-16
- Migrated raw JSON flat file persistence in `simulator_core.py` to a robust SQLite database (`data/simulator.db`) to safely handle concurrency across multi-user environments.
- Decoupled `create_team`, `create_bridge_agent`, and `create_judge_agent` from the massive `app.py` monolith into a dedicated `services/agents.py` module.

## 0.23.3 - 2026-04-16
- Verified that `replay_mode` UI in `app.py` is entirely complete and does not rely on a missing `replay_run` function. Replays are fully functional through `build_replay_text`.
- Refactored `fetch_webpage` in `simulator_tools.py` to utilize `httpx.AsyncClient` natively, improving Chainlit event loop concurrency.

## 0.23.2 - 2026-04-16
- Verified that `replay_mode` and all related export browsing functions (`/replays`, `/replay-open`, `/replay-step`, `/compare`) are already fully integrated and functional per user request.

## 0.23.1 - 2026-04-16
- Verified that `/room-analytics [name]` is already fully integrated and functional per user request. No codebase modifications were required to satisfy the operational insight analytics.

## 0.23.0 - 2026-04-13
- Finalized analysis and ideation phase. Added `IDEAS.md` documenting architectural refactors, UI polishing, and product pivots for future development iterations.

## 0.22.1 - 2026-04-13
- Added robust user authentication via `cl.password_auth_callback` mapping to `AGENTIRC_USER_<USERNAME>` env vars.
- Added safe sandbox read/write tool integrations.
- Added extended unit test coverage for custom connectors.
- Decoupled model configurations to external files.

# Changelog

## [0.46.0] - 2024-06-30
### Added
- Finished working on IDEAS.md functionality:
  - Fixed headless IRC `headless_irc.py` merge conflicts and integration.
  - Implemented bi-directional Discord bot bridge scaffolding in `discord_bridge.py`.
  - Added CSS CRT shader effect to `public/irc.css`.
  - Added GitHub PR Review Agents script scaffold in `pr_review_agents.py` utilizing `SelectorGroupChat`.
  - Added `/go` MMORPG mechanics to `app.py` for room exploration and AI NPC roleplay overrides.


## 0.20.0 - 2026-04-13
- Added configurable providers and models (`agents_config.json`, `config.toml`).
- Added web search and webpage fetching capabilities via `duckduckgo-search` and `markdownify`.
- Implemented `/slap` tool for the 1990s IRC interface.
- Enabled file and image upload processing, forwarding them as multimodal payloads to the agents.
- Updated system instructions to enforce authentic model personas and immediately emit topic on room activation.
- Extensively expanded project documentation (TODO.md, ROADMAP.md, VISION.md, MEMORY.md, DEPLOY.md, LLM instructions).


## 0.19.0 - 2026-04-05
- Added `/leaderboard` for session-wide room and agent rankings by message volume, tokens, and cost.
- Added live behavior tests for the `webhook` connector using a local threaded HTTP server.
- Added live behavior tests for the `websocket` bridge runtime using a local threaded WebSocket server.
- Refined unit tests and helper assertions for metrics and external payload delivery.
- Expanded unit coverage from 44 to 48 tests.
- Updated README, findings, design, implementation, testing, and handoff documentation for leaderboards and endpoint-backed validation.

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

## 0.42.0 - 2026-06-22
- Synced upstream repository and merged remote feature branches locally.
- Forward merged active features to `main` branch.
- Updated version numbering to 0.42.0.

## 0.42.1 - 2026-06-24
- Synced upstream repository and `.jules` session cache into working tree.
- Updated version metadata to 0.42.1.

## 0.43.0 - 2026-06-25
- Implemented `headless_irc.py`, an autonomous background script that connects to external IRC servers natively.

## 0.44.0 - 2026-06-25
- Developed and integrated a FastMCP implementation in `mcp_server.py` to seamlessly expose `TOOL_CATALOG` functions natively over MCP standard out.
- Added `mcp` explicitly to `requirements.txt`.

## 0.44.1 - 2026-06-25
- Verified `deliver_to_mcp` in `bridge_connectors.py` strictly adheres to JSON-RPC 2.0 payloads for outbox messages per the Nudge request.

## 0.44.2 - 2026-06-25
- Ensured MCP compliance in `deliver_to_mcp` by confirming the implementation correctly encapsulates outbox messages inside strict JSON-RPC 2.0 envelopes.

## 0.44.3 - 2026-06-25
- Ensured MCP compliance in `simulator_tools.py` tools according to the Nudge request.

## 0.45.0 - 2026-06-25
- Began implementation of full multi-room real-time websocket bridging UI, starting with routing enhancements in `simulator_core.py`.

## 0.44.4 - 2026-06-25
- Verified and finalized the MCP compliance updates across `bridge_connectors.py` and `simulator_tools.py`.

## 0.44.5 - 2026-06-25
- Finalized UI retro tool call execution visual rendering in `app.py`.

## 0.45.1 - 2026-06-25
- Reviewed MCP connector in `bridge_connectors.py` and validated full JSON-RPC 2.0 encapsulation.

## 0.45.2 - 2026-06-25
- Started working on Full multi-room real-time websocket bridging UI in `app.py`.

## 0.46.0 - 2026-06-25
- Started working on Full multi-room real-time websocket bridging UI.

## 0.45.4 - 2026-06-25
- Started working on Full multi-room real-time websocket bridging UI.

## 0.45.5 - 2026-06-26
- Verified that external bridge payloads appropriately marshal full transcript context data from `simulator_core.py` enabling real-time websocket integration with downstream components like React and Chainlit.

## 0.45.6 - 2026-06-26
- Finalizing the websocket bridging UI layout in `app.py`.

## 0.45.7 - 2026-06-26
- Added `/bridge-websocket` command implementation to `app.py` UI logic.

## 0.45.8 - 2026-06-26
- Validated that the multi-room real-time websocket bridging UI layout conforms to the AgentIRC design and roadmap.

## 0.46.5 - 2026-06-27
- Refined terminal status to ignore garbage supervisor prompts and ensure proper workflow completion state in master.
