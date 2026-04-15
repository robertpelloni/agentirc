# AgentIRC IDEAS & Improvement Log

## Architectural Improvements
- **Database Migration:** Currently, the system persists state heavily in flat `.json` files inside the `data/` directory (e.g., `state_admin.json`). Moving to SQLite (via SQLAlchemy) would solve potential concurrency issues when users spawn multiple browser tabs hitting the same session files.
- **Microservice Decoupling:** `app.py` is huge (1400+ lines). The UI logic (Chainlit message hooks) should be separated from the internal AutoGen agent instantiation code. A `services/agents.py` module could own `create_team` and `stream_agent`.
- **Async I/O in Tools:** `fetch_webpage` in `simulator_tools.py` uses synchronous `requests.get()`. This blocks the async event loop during execution, potentially slowing down Chainlit. Migrating to `aiohttp` or `httpx` would greatly improve latency.

## Product Pivots & Expansions
- **MMORPG Mechanics:** Instead of a generic IRC clone, pivot the platform toward a text-based Multi-User Dungeon (MUD). Add a `/go` command, create interconnected 'rooms' as geographic locations, and let the LLMs roleplay as NPCs in the environment.
- **GitHub PR Review Agents:** Instead of chatting, users could paste a GitHub PR link. The `/bridge-roles` system could spawn 5 agents (Critic, Security Expert, QA, Junior Dev, Tech Lead) that argue over the PR, fetch the diff, and emit a final consensus.
- **Discord/Slack Bridge:** Using the existing `bridge_connectors.py` outbox system, build a live Discord bot that bi-directionally mirrors the `RoundRobinGroupChat` to an actual Discord server so humans can chat with the models from their phones without logging into Chainlit.

## Frontend UI Refinements
- **Authentic Terminal CRT Shader:** Include a WebGL or heavy CSS CRT shader in `public/style.css` to add scanlines, phosphor glow, and screen curvature to fully sell the 90s aesthetic.
- **Custom Audio Engine:** The current `cl.Audio` method was suspended because Chainlit binds audio to visible message blocks. Writing a custom React component for Chainlit (or injecting a raw HTML/JS audio orchestrator in `index.html`) to listen for websocket events and play `/sounds/beep.wav` silently in the background would complete the feature smoothly.
- **Typing Indicators:** IRC didn't have typing indicators, but it would be useful to see which specific agent is currently 'thinking' rather than waiting silently.
