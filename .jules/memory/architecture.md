Hello! I'm Jules, your AI coding agent. I've reviewed the project memory for AgentIRC to get us aligned on the architecture and workflow. Here is the comprehensive summary:



# Comprehensive Project Summary: AgentIRC

## 1. Architecture & Core Components
The project is an IRC-style multi-model simulation environment designed to bring multiple autonomous AI agents together into a unified, 1990s retro-styled chat interface.
* **Frontend/UI (`app.py` & Chainlit):** Acts as the primary UI gateway using Chainlit. It handles command dispatching (e.g., `/topic`, `/slap`, `/poll`), multi-modal file uploads (converting images for AutoGen), and renders the UI. It relies on a custom CSS CRT shader (`public/style.css`) for authentic 90s terminal aesthetics (scanlines, phosphor flicker).
* **Domain Logic (`simulator_core.py`):** Manages room transitions, state definitions, telemetry, cost tracking, replay utilities, and transcript parsing.
* **Agent Orchestration (`services/agents.py`):** Utilizes AutoGen (v0.4+) to instantiate `AssistantAgent`s and coordinate them via `RoundRobinGroupChat` or `SelectorGroupChat`.
* **Tool Catalog (`simulator_tools.py`):** Centralizes tools available to agents (e.g., `fetch_webpage`, `web_search`). Crucially, all tools here must utilize asynchronous I/O (e.g., `httpx.AsyncClient` or `anyio.to_thread`) to prevent blocking Chainlit's main async event loop.
* **External Bridging (`bridge_connectors.py` & Runtimes):** Supports routing payloads in/out of the simulator (outbox/inbox/processed) to external services, including fully formatting payloads for Discord webhooks (respecting the 2000 character limit).

## 2. State Management & Persistence
* **Database & Concurrency:** State persistence is handled via a unified SQLite database (`data/simulator.db`), storing state JSON BLOBs keyed by the authenticated username to safely support multi-user concurrency and session segregation.
* **Configuration:** Core simulator states (enabled agents, custom aliases, room topics, lineups, and enabled tools) are loaded and saved dynamically, divorcing runtime configuration from hardcoded parameters.

## 3. Key Features & Design Patterns
<<<<<<< HEAD
* **Dynamic Modding & Admin UI:**
=======
* **Dynamic Modding & Admin UI:**
>>>>>>> origin/jules-agentirc-async-refactor-1797650712095433665
  * Models can be added at runtime via the `/add-model` command (parsing arguments via `shlex` and updating `AGENT_SPECS`).
  * A dedicated **Admin UI** integrates directly into Chainlit's `ChatSettings` modal (`@cl.on_settings_update` in `app.py`), allowing real-time toggling of active agents and `TOOL_CATALOG` functions without restarting the server.
* **Scenarios & Roleplay Constraints:**
  * **MUD Mechanics:** The `/go <room>` command transitions the simulator into `mud_exploration` mode, forcing agents to roleplay as environmental NPCs in a text-based adventure.
  * **Operator Polling:** The `/poll` command streams a markdown voting UI into the context, forcing agents to vote on user-defined topics.
  * **PR Review:** A specific scenario utilizing the `fetch_github_pr` async tool to evaluate GitHub diffs using personas like 'Security_Auditor'.
  * **Strict Persona Directives:** System prompts rigidly enforce that agents act as themselves and *never* hallucinate fake IRC users or simulate multi-party conversations on their own.
* **Vision & Multi-modal Support:** The application inherently handles multi-modal capabilities. Uploaded image files through the Chainlit UI are intercepted in the `@cl.on_message` handler and translated accurately into `autogen_core.Image.from_file()` objects using PIL, enabling vision-capable models to view files directly within the task array.

## 4. Technical Constraints & Decisions
* **Python 3.14.3 (Experimental):** The project targets this specific Python build, which requires extreme care. Explicit `asyncio` and `anyio` patches exist in `run.py` and `app.py` to prevent breaking Chainlit and AutoGen's background task loops.
* **Context Window Protection:** To prevent token bloat and performance degradation, default enabled agents are capped at 10. The system dynamically injects brevity notes into prompts when rooms are highly populated. File system access is strictly restricted to an isolated `.sandbox/` directory.

## 5. Workflow & Governance Directives
* **Continuous Execution:** Implementors operate on an autopilot directive: pull/sync upstream, merge local branches, execute features, sync docs, and commit autonomously without pausing for confirmation.
* **Documentation Dominance:** A rigorous documentation standard is enforced. Any major change requires immediate, synchronized updates across `VISION.md`, `ROADMAP.md`, `CHANGELOG.md`, `TODO.md`, `MEMORY.md`, `DEPLOY.md`, and `HANDOFF.md`.
* **Versioning:** The project relies on a single source of truth for versions tracked in `VERSION` and `VERSION.md`. Every release bump must reflect across all docs and be referenced in git commit messages.
* **Pre-commit Integrity:** All new features must pass rigorous verification, including localized testing (`PYTHONPATH=. python -m pytest tests/`), frontend verification (if applicable), simulated code reviews, and structured memory recordings before finalizing the implementation.