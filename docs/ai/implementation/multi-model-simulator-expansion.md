# Multi-Model Simulator Expansion

## Summary
This implementation pass extends AgentIRC beyond bridge agents into external bridge foundations by adding standardized outbox payload generation for future websocket and IRC connectors.

## Newly Added Capabilities
### External Bridge Foundations
- `/bridge-export <room> [count]`
- `/outbox`
- standardized `room_snapshot` payload generation
- standardized `bridge_note` payload generation helper
- JSON outbox file writing under `outbox/`
- outbox listing helper for operator inspection

### Telemetry Enhancements
- external-export telemetry counter
- dashboard and observer surfaces now reflect external export activity
- export metadata now includes external export counters

## Implementation Notes
### `simulator_core.py`
This module now additionally owns:
- external room payload builders
- external bridge payload builders
- outbox payload writing helpers
- outbox listing/rendering helpers
- external export telemetry updates

### `app.py`
This module now additionally handles:
- `/bridge-export <room> [count]`
- `/outbox`
- outbox payload generation from room state
- external-export telemetry updates on the exported room

## Findings and Analysis
### 1. File-based outbox payloads are the right first connector foundation
They create a stable integration boundary without prematurely introducing network daemons or runtime bridge complexity.

### 2. External integration should start with schemas, not sockets
A well-defined payload contract is more valuable early than a half-finished live transport layer.

### 3. Bridge workflows are now layered
The simulator now supports:
- deterministic bridge notes
- model-generated bridge notes
- external payload export for future bridge runtimes

## Recommended Follow-Up
- external IRC/websocket bridge runtime on top of `outbox/`
- richer observer/dashboard views with live metrics panels
- role-specific bridge agents and routing policies
- opt-in integration tests for live scheduling, room switching, bridge delivery, bridge-AI generation, external export, and streaming
