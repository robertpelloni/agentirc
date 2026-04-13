# Handoff Notes

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
# Handoff Document

- Implemented configurable providers via `agents_config.json` and `config.toml`.
- Added web search tools (`duckduckgo-search`) and markdown fetch tools (`markdownify`).
- Implemented `/slap` tool in the IRC interface.
- Added image upload processing for Chainlit to pass multimodal payloads to agents.
- Updated system prompts to enforce authentic model personalities.
- Prepared comprehensive documentation update.
