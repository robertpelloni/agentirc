# Agent Memory & Observations

- **Codebase Pattern**: `app.py` handles Chainlit specific UI and event routing. `simulator_core.py` handles pure Python data manipulation, state management, and text formatting.
- **Design Preferences**: The user loves deep, comprehensive documentation and retro 90s aesthetics. Always over-communicate in documentation and strictly adhere to monospace, dark backgrounds, and neon text for the UI.
- **Testing**: Tests are in `tests/` and use `unittest`.
# AgentIRC Memory

- Code is structured primarily around `simulator_core.py` for logic and state, and `app.py` for Chainlit UI.
- We rely heavily on AutoGen for multi-agent workflows.
- Python 3.14.3 compatibility remains slightly brittle; keep an eye on `asyncio` patches.
- The UI mimics a 90s terminal via custom CSS in `public/style.css`.
