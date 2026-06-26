[PROJECT_MEMORY]

### Architecture & Patterns
- **Orchestration Layer**: The project utilizes **Microsoft AutoGen (0.4+)** to construct multi-agent simulations. Agents (defined via `AssistantAgent`) coordinate via `RoundRobinGroupChat` (in broadcast mode) or `SelectorGroupChat` (in discuss mode).
- **Presentation Layer**: Built on **Chainlit**. The UI forces an authentic 1990s IRC aesthetic using extensive CSS overrides (`public/style.css`), such as monospaced fonts, classic color schemes, specific scrollbars, hiding avatars, and prefixing author tags with `<Nickname>`.
- **Logic Segregation**:
  - `app.py`: Acts as the presentation entrypoint. Manages UI wiring, async Chainlit event loops (`@cl.on_chat_start`, `@cl.on_message`), settings callbacks (`@cl.on_settings_update`), and model streaming orchestration.
  - `simulator_core.py`: Encapsulates pure business logic. Handles transcript parsing, room state definitions, multi-room context shifting, data persistence (`simulator_state.json`), and markdown text string constructions.
  - `simulator_tools.py`: Connects AutoGen function-calling to actual implementations, such as the `web_search` and `fetch_webpage` features introduced to mimic MCP tool accessibility natively.
- **State Management**: State mutability is completely data-driven. Configs, model specs, custom aliases, room topics, and lineups are loaded/saved directly into `data/simulator_state.json`, divorcing configuration from hardcoded parameters.

### Key Technical Decisions
- **Persistent Rosters via UI**: Moving `AGENT_SPECS` to persistent storage allows models and providers (e.g., OpenRouter variants) to be dynamically added or enabled/disabled via Chainlit UI `ChatSettings` and commands like `/add-model` at runtime.
- **Strict Persona Directives**: System prompts explicitly tell the LLMs to act as themselves and forbid them from hallucinating fake multi-user IRC conversations. They are just participants reacting to the configured room topic.
- **Multi-Modal Support via Chainlit**: Uploaded files and images in Chainlit are intercepted in `on_message` and translated correctly into `autogen_core.Image` representations if vision models are enabled.
- **Documentation Dominance**: A heavy emphasis on deep documentation. Root files (`VISION.md`, `ROADMAP.md`, `CHANGELOG.md`, `DEVOPS.md`, `INSTRUCTIONS.md`) operate as strict architectural and contextual anchors for future AI implementors iterating on the codebase.
- **Synchronous Compatibility**: The integration of Chainlit with AutoGen 0.4+ under Python 3.14 requires explicit `anyio.to_thread` patches in `run.py`/`app.py` to circumvent async environment crashes. Synchronous mutations inside `app.py` were carefully decoupled from async UI updates.
