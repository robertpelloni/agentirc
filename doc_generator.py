import os
import json

def write_doc(filename, content):
    with open(filename, 'w') as f:
        f.write(content)

write_doc('VISION.md', """# AgentIRC Vision

AgentIRC is an IRC-style multi-model simulation environment designed to bring multiple AI agents together into a unified chat interface, styled after 1990s IRC clients.

## Goals
- **Total Configurability**: Providers and models should be entirely customizable through the UI, allowing integration of any OpenRouter or other OpenAI-compatible API endpoints.
- **Genuine Personas**: Models speak as themselves, developed through training, not simulating "fake" IRC conversations or multiple users.
- **Classic UI**: The frontend uses Chainlit heavily customized with CSS to look like a classic 90s IRC terminal.
- **Rich Tools**: Native tools like Web Search (via DuckDuckGo) and Webpage-to-Markdown fetching, as well as Memory tools.
- **Robustness**: Maintain comprehensive persistence, logging, telemetry, and room management.

## Roadmap & Execution
We are currently in a high-iteration phase, implementing features like vision model support, MCP tools, and external bridging.
""")

write_doc('DEVOPS.md', """# DevOps & Deployment

## Environment Setup
- Python 3.14+ recommended.
- Install dependencies: `pip install -r requirements.txt`.
- Copy `.env.example` to `.env` and fill `OPENROUTER_API_KEY`.

## Running the App
- Run `chainlit run app.py -w` to start the web interface.

## Tests
- Run `python -m unittest discover tests` to ensure core logic operates correctly.

## State Management
- `simulator_state.json` persists lineups, personas, jobs, and agent configurations. Ensure this file is backed up.
""")

write_doc('CHANGELOG.md', """# Changelog

## [1.1.0] - 2026-04-10
### Added
- Fully configurable agent roster via `simulator_state.json` and UI.
- Chat topic configuration in the Settings panel, fed directly to the agents.
- Vision support: Passing uploaded images to AutoGen agents.
- Web search tool using DuckDuckGo.
- Webpage fetcher (converts HTML to Markdown).
- IRC commands `/slap` and `/me`.
- Extensive documentation overhaul (VISION.md, CHANGELOG.md, etc.).

### Changed
- System prompt heavily updated to force models to act as themselves and not simulate a fake IRC room.
- Global `AGENT_SPECS` refactored into persistent state for UI mutability.
- Further styling adjustments for 1990s IRC aesthetic.
""")

write_doc('VERSION', "1.1.0\n")

write_doc('ROADMAP.md', """# Roadmap

## Short Term
- Complete integration tests for new `/add-model` command.
- Refine external bridge payloads (MCP compliance).
- Enhance UI feedback for tool calls in the retro aesthetic.

## Medium Term
- Full multi-room real-time websocket bridging UI.
- Support for local LLMs via Ollama natively in the UI config.

## Long Term
- A fully headless mode driven entirely by IRC clients.
- Advanced agent autonomous scheduling with persistent memory.
""")

write_doc('TODO.md', """# TODO List

- [x] Refactor Agent Specs to persistent state.
- [x] Add Chat Settings UI for topic and toggles.
- [x] Add `/add-model` command.
- [x] Update system prompt to prevent simulated users.
- [x] Add `/slap` and `/me`.
- [x] Add Web Search and Web Fetch tools.
- [x] Add Vision support for images.
- [x] 90s CSS Styling.
- [x] Extensive Documentation.
- [ ] Add more comprehensive tests for vision processing.
- [ ] Implement true native MCP server support.
- [ ] Create a dedicated Admin UI for tool management.
""")

write_doc('HANDOFF.md', """# Handoff Notes

## Current State
The project has been significantly updated.
- Models are now dynamically loaded from `simulator_state.json`.
- The UI exposes a settings panel for toggling agents and changing topics.
- Web search and page fetching tools are integrated.
- Image uploads are routed to AutoGen as `Image` objects.
- System prompts are strict about persona adherence.
- All tests pass (except those explicitly skipped for live integration).

## Next Implementor
When taking over, please review `ROADMAP.md` and `TODO.md`. The next major steps involve native MCP server integration and more robust testing for the vision endpoints.
""")

write_doc('MEMORY.md', """# Agent Memory & Observations

- **Codebase Pattern**: `app.py` handles Chainlit specific UI and event routing. `simulator_core.py` handles pure Python data manipulation, state management, and text formatting.
- **Design Preferences**: The user loves deep, comprehensive documentation and retro 90s aesthetics. Always over-communicate in documentation and strictly adhere to monospace, dark backgrounds, and neon text for the UI.
- **Testing**: Tests are in `tests/` and use `unittest`.
""")

write_doc('INSTRUCTIONS.md', """# Universal LLM Instructions

When working on this repository, you must adhere to the following rules:
1. **Never break the 90s aesthetic**: Any new UI elements must use the classes and styles defined in `public/style.css`.
2. **Keep Core Logic Isolated**: Do not put complex business logic in `app.py`. Put it in `simulator_core.py` and test it in `tests/`.
3. **Always Update Docs**: Every feature must be documented in `CHANGELOG.md`, `ROADMAP.md`, `TODO.md`, and the version bumped in `VERSION`.
4. **Agent Integrity**: Do not prompt the agents to roleplay as fake users; they must roleplay as themselves (the model).
""")

for f in ['CLAUDE.md', 'AGENTS.md', 'GEMINI.md', 'GPT.md', 'copilot-instructions.md']:
    write_doc(f, "Please refer to `INSTRUCTIONS.md` for the universal guidelines when modifying this codebase.\n")

print("Documentation generated.")
