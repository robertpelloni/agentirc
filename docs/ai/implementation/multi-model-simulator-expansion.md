# Multi-Model Simulator Expansion

## Summary
This implementation pass extends AgentIRC beyond runtime scaffolding into a cleaner external connector architecture with inbox support, runtime status, and a connector adapter layer.

## Newly Added Capabilities
### External Connector Runtime Expansion
- `bridge_connectors.py`
- connector catalog text for operator inspection
- connector routing support for `console`, `inbox`, and `jsonl`
- `bridge_runtime.py --connector <name>` support
- `/connectors`

### Bidirectional Bridge Workflow
- `/bridge-runtime`
- `/inbox`
- `/import-bridge <file> [room]`
- manual import of inbound payloads into room history
- runtime status visibility from inside the app

## Implementation Notes
### `simulator_core.py`
This module now additionally owns:
- inbox and processed directory concepts
- inbox payload listing helpers
- bridge runtime status rendering
- external payload loading helpers
- imported-payload rendering helpers
- external import telemetry updates

### `bridge_connectors.py`
This new module owns:
- connector catalog metadata
- connector catalog rendering
- payload routing functions
- delivery helpers for console, inbox, and JSONL outputs

### `bridge_runtime.py`
This module now additionally handles:
- pluggable connector routing
- connector selection through CLI arguments
- richer runtime status including connector mode

### `app.py`
This module now additionally handles:
- `/connectors`
- `/bridge-runtime`
- `/inbox`
- `/import-bridge <file> [room]`
- room-local insertion of imported external payloads
- external import telemetry updates

## Findings and Analysis
### 1. Connector adapters are the right next abstraction after a raw runtime scaffold
They create a clean seam for future transport implementations without overcoupling transport logic to runtime polling.

### 2. Bidirectional external flow matters more than export alone
Once payload export exists, inbox import is the natural next step because it starts making external systems feel part of the simulator rather than mere outputs.

### 3. Runtime observability is still critical at scaffold level
Directory counts, runtime mode, processed payloads, and JSONL logs are already valuable signals before true live transports exist.

## Recommended Follow-Up
- external IRC/websocket bridge runtime on top of the connector layer
- richer observer/dashboard views with live metrics panels
- role-specific bridge agents and routing policies
- opt-in integration tests for bridge runtime processing, bridge import, and live streaming
