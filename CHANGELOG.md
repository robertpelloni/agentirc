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
