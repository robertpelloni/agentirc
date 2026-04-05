# Multi-Model Simulator Expansion

## Summary
This implementation pass extends AgentIRC beyond replay and scheduling into a more complete simulation operations console with hybrid cost tracking, replay comparison, and reusable autonomous jobs.

## Newly Added Capabilities
### Hybrid Cost Tracking
- `/costs` command for session-level and per-agent cost visibility
- pricing hints attached to agent specs
- usage extraction from streamed events when available
- fallback token estimation when provider usage metadata is absent
- actual-cost and estimated-cost tracking side by side

### Replay Comparison
- `/compare <left> <right> [count]`
- support for `latest` and `previous` replay resolution
- side-by-side transcript excerpt comparison from exported JSON artifacts
- replay comparison telemetry counter

### Reusable Autonomous Jobs
- `/jobs`
- `/save-job <name>`
- `/run-job <name>`
- `/delete-job <name>`
- local persistence of automation presets tied to simulator config

## Implementation Notes
### `simulator_core.py`
This module now additionally owns:
- hybrid usage parsing and cost calculation helpers
- replay comparison helpers
- saved job persistence helpers
- comparison telemetry helpers
- richer per-agent telemetry shape

### `app.py`
This module now additionally handles:
- pricing hints for active model lineup
- `/costs`, `/jobs`, `/save-job`, `/run-job`, `/delete-job`, and `/compare`
- judge pricing hinting
- usage extraction from streamed events before telemetry updates

## Findings and Analysis
### 1. Hybrid cost tracking is more honest than fake precision
Provider usage metadata is not guaranteed across all model backends, so the simulator now explicitly distinguishes between actual cost and estimated cost instead of pretending heuristics are authoritative.

### 2. Replay comparison is the natural next step after replay
Once replay existed, comparison became the highest-value follow-up because operators need to inspect differences across runs, not just reopen individual transcripts.

### 3. Saved jobs are the right level of automation persistence
Persisting reusable job presets gives strong operator leverage without prematurely building a full scheduler service.

## Recommended Follow-Up
- interactive replay stepping UI
- multi-room orchestration
- external IRC/websocket bridge support
- opt-in integration tests for live scheduling and streaming
