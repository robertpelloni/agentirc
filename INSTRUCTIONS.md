# Universal LLM Instructions

When working on this repository, you must adhere to the following rules:
1. **Never break the 90s aesthetic**: Any new UI elements must use the classes and styles defined in `public/style.css`.
2. **Keep Core Logic Isolated**: Do not put complex business logic in `app.py`. Put it in `simulator_core.py` and test it in `tests/`.
3. **Always Update Docs**: Every feature must be documented in `CHANGELOG.md`, `ROADMAP.md`, `TODO.md`, and the version bumped in `VERSION`.
4. **Agent Integrity**: Do not prompt the agents to roleplay as fake users; they must roleplay as themselves (the model).
