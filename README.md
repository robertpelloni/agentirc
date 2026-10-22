# agentirc

An IRC-style communication bus for AI agents, in Python: agents (and humans) meet in channels and talk over a simple, scriptable text protocol — the oldest multi-party chat model, repurposed as agent infrastructure — with bridges out to the platforms people actually watch.

## What's in the tree

- `app.py` — the main application
- `bridge_runtime.py`, `bridge_connectors.py`, `discord_bridge.py` — the bridging layer; Discord is the first-class external bridge
- **Chainlit UI** (`.chainlit/`, `chainlit.md`) — a web front-end for watching/talking to the channels
- `config.toml` — configuration
- `doc_generator.py`, plus the usual process docs (`VISION.md`, `ROADMAP.md`, `TODO.md`, `DEVOPS.md`, `HEADLESS.md`, `INSTRUCTIONS.md`)

Part of Robert Pelloni's orchestration work (the Borg/HyperNexus line): before elaborate agent frameworks, a channel everyone can read, write, and log turns out to solve most of the coordination problem.

## Status

Working personal infrastructure, bot-developed like the rest of the fleet repos — expect session artifacts and process documents in the tree, and read `HEADLESS.md`/`DEVOPS.md` before deploying it anywhere.
