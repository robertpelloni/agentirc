# Changelog

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
## 0.20.0 - 2026-04-10
- Added configurable providers and models (`agents_config.json`, `config.toml`).
- Added web search and webpage fetching capabilities via `duckduckgo-search` and `markdownify`.
- Implemented `/slap` tool for the 1990s IRC interface.
- Enabled file and image upload processing, forwarding them as multimodal payloads to the agents.
- Updated system instructions to enforce authentic model personas and immediately emit topic on room activation.
- Extensively expanded project documentation (TODO.md, ROADMAP.md, VISION.md, MEMORY.md, DEPLOY.md, LLM instructions).


## 0.19.0 - 2026-04-05
- Added `/leaderboard` for session-wide room and agent rankings by message volume, tokens, and cost.
- Added live behavior tests for the `webhook` connector using a local threaded HTTP server.
- Added live behavior tests for the `websocket` bridge runtime using a local threaded WebSocket server.
- Refined unit tests and helper assertions for metrics and external payload delivery.
- Expanded unit coverage from 44 to 48 tests.
- Updated README, findings, design, implementation, testing, and handoff documentation for leaderboards and endpoint-backed validation.

### Changed
- System prompt heavily updated to force models to act as themselves and not simulate a fake IRC room.
- Global `AGENT_SPECS` refactored into persistent state for UI mutability.
- Further styling adjustments for 1990s IRC aesthetic.
