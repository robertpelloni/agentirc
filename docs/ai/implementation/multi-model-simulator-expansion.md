# Multi-Model Simulator Expansion

## Summary
This implementation pass extends AgentIRC beyond runtime scaffolding into a cleaner external connector architecture with inbox support, runtime status, a connector adapter layer, prompt-interval auto-bridge policies, and persistent room archives.

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

## Auto-Bridge and Room Archive Expansion
### Auto-Bridge Policies
- `/auto-bridge`
- `/auto-bridge <target> <interval> [note|ai] [role] [focus]`
- `/auto-bridge stop`
- prompt-interval policy execution using deterministic or AI bridge delivery

### Persistent Room Archives
- `/archives`
- `/archive-room [name]`
- `/restore-room <archive> [room]`
- room snapshots saved to `data/archives/`

## Findings and Analysis
### 4. Auto-bridge is the natural next layer after manual bridge commands
Manual bridge commands prove the workflow; auto-bridge turns it into a repeatable room policy.

### 5. Room archives are the right first step before full persistent room state
Explicit archive/restore commands preserve operator control while still giving durable scenario snapshots.

## Saved Auto-Bridge Policy Expansion
### Reusable Policy Presets
- `/bridge-policies`
- `/save-bridge-policy <name>`
- `/load-bridge-policy <name>`
- `/delete-bridge-policy <name>`
- persistent storage of auto-bridge settings inside `data/simulator_state.json`

## Findings and Analysis
### 6. Saved auto-bridge policies are the right next step after one-off auto-bridge configuration
Once prompt-interval bridge automation exists, operators quickly need reusable presets for recurring workflows.

## Recommended Follow-Up
- external IRC/websocket bridge runtime on top of the connector layer
- richer observer/dashboard views with live metrics panels
- role-specific bridge agents and routing policies
- opt-in integration tests for bridge runtime processing, bridge import, live streaming, auto-bridge execution, room archive restore, and saved bridge policies
