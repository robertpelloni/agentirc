# Multi-Model Simulator Expansion

## Summary
This implementation pass extends AgentIRC beyond telemetry and judging into a more complete simulation operations console with autonomous scheduling and replay support.

## Newly Added Capabilities
### Autonomous Scheduling
- `/schedule` status command
- `/schedule <seconds> [runs]` for bounded autonomous simulation loops
- `/schedule stop` to stop the active schedule
- autonomous prompt generation based on current topic, scenario, and mode
- schedule status tracked in live session config

### Replay Support
- `/replays` to list exported JSON replay sources
- `/replay [latest|file.json] [count]` to inspect prior transcript excerpts
- JSON export discovery and replay payload loading helpers
- replay-view telemetry

### Telemetry Enhancements
- scheduled-run telemetry
- replay-view telemetry
- judge prompts no longer distort broadcast/discuss counters
- richer status surface including schedule state

## Implementation Notes
### `simulator_core.py`
This module now additionally owns:
- automation configuration defaults and status rendering
- autonomous prompt construction
- scheduled-run telemetry updates
- replay file discovery and loading
- replay rendering helpers

### `app.py`
This module now additionally handles:
- a session-scoped asyncio automation task
- autonomous schedule lifecycle commands
- replay commands wired to export artifacts
- automation-task cleanup on chat end and reset

## Findings and Analysis
### 1. Export artifacts became more valuable once replay existed
JSON transcript exports are no longer just archival outputs. They now act as lightweight replay artifacts, which increases the value of consistent transcript formatting and export metadata.

### 2. Bounded scheduling is the safest first automation model
A schedule that requires both an interval and a bounded run count is significantly safer than unconstrained autonomous looping. It reduces the risk of runaway costs and keeps operator intent explicit.

### 3. Replay and scheduling reinforce each other
Scheduling produces structured repeated runs; replay makes those runs reviewable. Together they move AgentIRC closer to a real simulation lab rather than a one-shot chat interface.

## Recommended Follow-Up
- provider-native token/cost accounting
- interactive replay stepping
- scheduled runs based on saved lineups and saved scenarios
- side-by-side comparison between two exported runs
- multi-room orchestration
