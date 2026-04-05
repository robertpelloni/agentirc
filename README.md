# AgentIRC: The Multi-Model Broadcast Network

AgentIRC is an IRC-style multi-model simulation environment built with **Microsoft AutoGen 0.4+**, **Chainlit**, and **OpenRouter**. It lets a human operator run coordinated conversations across multiple model personas, switch between broadcast and discussion modes, inspect telemetry, persist lineups/personas/jobs, export transcripts, replay and compare old runs, estimate costs, and trigger autonomous scheduled simulations.

## 🚀 Feature Overview

### Core Simulation
- **Broadcast Mode**: Every user prompt triggers one pass through the active model lineup.
- **Discuss Mode**: Models can deliberate, disagree, and build on each other over configurable turn counts.
- **Direct Messages**: `@AgentName <message>` targets one model without broadcasting to the full room.
- **Scenario Presets**: Switch quickly between `omni`, `debate`, `incident`, `redteam`, `worldbuild`, `product`, and `council`.
- **Moderator Modes**: Apply conversation-wide behavioral shaping with `off`, `facilitator`, `strict`, `critic`, and `chaos`.

### Agent Control
- **Dynamic Lineup Management**: Enable or disable agents at runtime.
- **Custom Persona Overrides**: Give individual agents new styles or roles on the fly and persist them across sessions.
- **Saved Lineups**: Save and reload named team configurations for recurring simulation setups.
- **Saved Jobs**: Save reusable autonomous schedules tied to current simulator settings and run them on demand.
- **Roster Inspection**: `/agents`, `/lineup`, and `/whois` expose bios, model IDs, enabled state, custom persona data, and pricing hints.

### Analysis & Operations
- **Session Status**: Inspect mode, scenario, moderator, lineup, job count, persistent-state counts, and cost summary.
- **Telemetry**: Per-agent response counts, character volume, token totals, average response latency, scheduled-run count, replay-view count, and comparison-view count.
- **Hybrid Cost Tracking**: Uses provider usage data when available and falls back to estimated tokens plus configurable pricing hints.
- **Analytics**: Aggregate session summaries, talkativeness ranking, output volume, autonomous-run volume, and last-prompt context.
- **Judge Evaluations**: Ask a dedicated judge model to assess recent transcript quality and propose next steps.
- **Replay Mode**: Browse exported JSON transcripts and replay the latest, previous, or named run as a transcript excerpt.
- **Replay Comparison**: Compare two exported runs side by side with `/compare`.
- **Autonomous Scheduling**: Queue repeated autonomous simulations on a timed interval with `/schedule` or run saved jobs with `/run-job`.
- **Transcript Export**: Export Markdown and JSON snapshots into `exports/`.
- **Persistent Logging**: Append IRC-formatted output to `irc_session.log`.

## 🧠 Architecture Notes
- **Chainlit session state** holds the live simulator config, transcript history, active team, persistent settings, and the current automation task handle.
- **`simulator_core.py`** isolates session defaults, command parsing, persona/lineup/job persistence, telemetry logic, cost tracking, replay helpers, comparison helpers, scheduling helpers, export helpers, and transcript formatting.
- **`app.py`** focuses on Chainlit wiring, AutoGen team construction, command dispatch, autonomous scheduling, replay/compare commands, and model streaming.
- **Persistent state** is stored in `data/simulator_state.json` and currently tracks saved lineups, persona overrides, and saved jobs.
- **Exports** include transcript content plus session telemetry snapshot so old runs can be replayed, compared, and analyzed.

## 🧪 Python 3.14 Compatibility
Operating on **Python 3.14.3** still requires defensive compatibility patching around `asyncio` / `anyio` behavior that can otherwise break Chainlit and related runtime assumptions. This project keeps those runtime patches in `run.py` and `app.py` to preserve execution under the current environment.

## 🛠 Tech Stack
- **Multi-Agent Orchestration**: AutoGen 0.4+
- **Web UI**: Chainlit
- **API Gateway**: OpenRouter
- **Runtime**: Python 3.14.3
- **Testing**: Python `unittest`

## 📋 Current Lineup
- **Claude 4.6** — nuanced perspectives
- **GPT-5.3** — advanced logic
- **Gemini 3.1** — fact-driven creativity
- **Grok 4.1** — rebellious wit
- **Qwen 3.6** — versatile power
- **Kimi 2.5** — optimized insights

## 💬 Command Reference
- `/help`
- `/mode <broadcast|discuss>`
- `/topic <text>`
- `/nick <name>`
- `/status`
- `/lineup`
- `/agents`
- `/whois <agent>`
- `/enable <agent>`
- `/disable <agent>`
- `/rounds <2-30>`
- `/scenario [name]`
- `/moderator [mode]`
- `/telemetry`
- `/analytics`
- `/costs`
- `/judge [focus]`
- `/personas`
- `/persona <agent> <text>`
- `/persona clear <agent>`
- `/lineups`
- `/save-lineup <name>`
- `/load-lineup <name>`
- `/delete-lineup <name>`
- `/jobs`
- `/save-job <name>`
- `/run-job <name>`
- `/delete-job <name>`
- `/schedule`
- `/schedule <seconds> [runs]`
- `/schedule stop`
- `/replays`
- `/replay [latest|previous|file.json] [count]`
- `/compare <left> <right> [count]`
- `/history [count]`
- `/export [md|json|both]`
- `/clear`
- `/reset`

## 📁 Important Files
- `app.py` - Chainlit app, command handling, AutoGen orchestration, autonomous scheduling, replay/compare commands, and judge execution.
- `run.py` - Python 3.14 compatibility launcher for Chainlit.
- `simulator_core.py` - Shared simulator logic, persistence, telemetry, hybrid cost tracking, analytics, replay helpers, job helpers, scheduling helpers, exports, and transcript utilities.
- `tests/test_simulator_core.py` - Regression coverage for helper-layer behavior.
- `docs/ai/design/simulator-operations.md` - feature-pass architecture notes and flow diagram.
- `docs/ai/implementation/` - implementation pass documentation.
- `docs/ai/testing/` - testing strategy and feature-specific verification notes.
- `data/simulator_state.json` - saved lineups, persona overrides, and saved jobs.
- `exports/` - generated transcript exports and replay source files.

## ⚡ Setup & Run
1. Add your OpenRouter key to `.env` as `OPENROUTER_API_KEY`.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Launch the simulator:
   ```bash
   python run.py
   ```
4. Run the tests:
   ```bash
   python -m unittest discover -s tests -v
   ```

## 🧭 Recommended Next Feature Passes
- multi-room/channel support
- interactive replay stepping UI
- external IRC / websocket bridging
- tool-use plugins and structured tasks
- side-by-side dashboard views
- opt-in live integration tests for Chainlit + provider calls
