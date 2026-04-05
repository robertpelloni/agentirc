# Multi-Model Simulator Expansion

## Summary
This implementation pass extends AgentIRC beyond external payload helpers into a fuller external bridge scaffold with runtime status, inbox support, import commands, and a standalone bridge runtime process.

## Newly Added Capabilities
### External Bridge Runtime Scaffold
- `bridge_runtime.py`
- polling of `outbox/`
- movement of processed payloads into `processed/`
- JSONL runtime event log generation
- `--once` mode for one-shot processing

### External Bridge Command Surface
- `/bridge-runtime`
- `/inbox`
- `/import-bridge <file> [room]`
- manual import of inbox payloads into rooms as system notes
- bridge runtime directory inspection from inside the app

### Telemetry Enhancements
- `external_imports` telemetry
- dashboards and observer view now surface import/export activity
- export metadata now includes import counters

## Implementation Notes
### `simulator_core.py`
This module now additionally owns:
- inbox/processed directory constants
- inbox payload listing helpers
- bridge runtime status rendering
- external payload loading helpers
- imported-payload rendering helpers
- external import telemetry updates

### `app.py`
This module now additionally handles:
- `/bridge-runtime`
- `/inbox`
- `/import-bridge <file> [room]`
- room-local insertion of imported external payloads
- external import telemetry updates

### `bridge_runtime.py`
This new module handles:
- one-shot or polling outbox processing
- payload movement to `processed/`
- runtime event logging
- basic status output for future connector expansion

## Findings and Analysis
### 1. A standalone runtime scaffold is the right bridge between payload contracts and live transports
It keeps the main app simple while enabling future external connector work.

### 2. Inbox support makes the bridge story bidirectional
Outbox-only support is useful, but inbox import is what starts making external integration feel real.

### 3. Runtime observability matters even for scaffolding
Directory counts, processed payloads, and runtime logs are already useful operator signals before live sockets exist.

## Recommended Follow-Up
- external IRC/websocket bridge runtime on top of the outbox/inbox contract
- richer observer/dashboard views with live metrics panels
- role-specific bridge agents and routing policies
- opt-in integration tests for bridge runtime processing, bridge import, and live streaming
