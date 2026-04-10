# AgentIRC Memory

- Code is structured primarily around `simulator_core.py` for logic and state, and `app.py` for Chainlit UI.
- We rely heavily on AutoGen for multi-agent workflows.
- Python 3.14.3 compatibility remains slightly brittle; keep an eye on `asyncio` patches.
- The UI mimics a 90s terminal via custom CSS in `public/style.css`.
