# AgentIRC: The Multi-Model Broadcast Network

AgentIRC is an IRC-style multi-model simulation environment built with **Microsoft AutoGen 0.4+**, **Chainlit**, and **OpenRouter**. It lets a human operator run coordinated conversations across multiple model personas, switch between broadcast and discussion modes, inspect telemetry, persist lineups/personas, export transcripts, and trigger judge-style evaluations over recent runs.

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
- **Roster Inspection**: `/agents`, `/lineup`, and `/whois` expose bios, model IDs, enabled state, and custom persona data.

### Analysis & Operations
- **Session Status**: Inspect mode, scenario, moderator, lineup, and persistent-state counts.
- **Telemetry**: Per-agent response counts, character volume, estimated tokens, and average response latency.
- **Analytics**: Aggregate session summaries, talkativeness ranking, output volume, and last-prompt context.
- **Judge Evaluations**: Ask a dedicated judge model to assess recent transcript quality and propose next steps.
- **Transcript Export**: Export Markdown and JSON snapshots into `exports/`.
- **Persistent Logging**: Append IRC-formatted output to `irc_session.log`.

## 🧠 Architecture Notes
- **Chainlit session state** holds the live simulator config, transcript history, active team, and loaded persistent settings.
- **`simulator_core.py`** isolates session defaults, command parsing, persona/lineup persistence, telemetry logic, export helpers, and transcript formatting.
- **`app.py`** focuses on Chainlit wiring, AutoGen team construction, command dispatch, and model streaming.
- **Persistent state** is stored in `data/simulator_state.json` and currently tracks saved lineups and persona overrides.
- **Exports** include both transcript content and a session telemetry snapshot to support replay or downstream analysis.

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
- `/judge [focus]`
- `/personas`
- `/persona <agent> <text>`
- `/persona clear <agent>`
- `/lineups`
- `/save-lineup <name>`
- `/load-lineup <name>`
- `/delete-lineup <name>`
- `/history [count]`
- `/export [md|json|both]`
- `/clear`
- `/reset`

## 📁 Important Files
- `app.py` - Chainlit app, command handling, AutoGen orchestration, telemetry updates, and judge execution.
- `run.py` - Python 3.14 compatibility launcher for Chainlit.
- `simulator_core.py` - Shared simulator logic, persistence, telemetry, analytics, exports, and transcript utilities.
- `tests/test_simulator_core.py` - Regression coverage for helper-layer behavior.
- `docs/ai/design/simulator-operations.md` - Feature-pass architecture notes and flow diagram.
- `docs/ai/implementation/` - Implementation pass documentation.
- `docs/ai/testing/` - Testing strategy and feature-specific verification notes.
- `data/simulator_state.json` - Saved lineups and persona overrides.
- `exports/` - Generated transcript exports.

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
- cost-aware model budgeting and throttling
- scheduled autonomous simulation runs
- replay mode for exported transcripts
- external IRC / websocket bridging
- tool-use plugins and structured tasks
- multi-room orchestration and observer dashboards
