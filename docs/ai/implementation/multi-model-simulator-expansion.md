# Multi-Model Simulator Expansion

## Summary
This implementation pass extends AgentIRC beyond deterministic bridge notes into richer observer tooling and model-generated cross-room bridge workflows.

## Newly Added Capabilities
### Observer Tooling
- `/observer`
- ranked multi-room operational view
- observer-view telemetry tracking
- richer visibility into room activity, prompts, bridges, and estimated cost

### Model-Generated Bridge Workflows
- `/bridge-ai <source> <target> [focus]`
- bridge-agent prompt construction from source room history
- AI-generated bridge note delivery into target room
- bridge-AI telemetry tracking
- bridge-agent cost tracking through the existing hybrid telemetry model

## Implementation Notes
### `simulator_core.py`
This module now additionally owns:
- observer rendering helpers
- bridge-agent prompt construction helpers
- bridge-AI and observer telemetry helpers
- expanded telemetry and analytics rendering for bridge-AI and observer usage

### `app.py`
This module now additionally handles:
- `/observer`
- `/bridge-ai <source> <target> [focus]`
- creation of a dedicated bridge agent using the configured judge model
- model-generated bridge-note insertion into target room history

## Findings and Analysis
### 1. Observer views are the right next step after dashboards
They provide a richer operational ranking surface without forcing a graphical dashboard redesign.

### 2. Bridge workflows benefit from dual modes
Deterministic bridges are cheap and predictable; model-generated bridges are richer and more abstract. Supporting both is a strong operator experience.

### 3. Bridge-agent costs fit naturally into the existing telemetry model
The bridge agent can reuse the same usage extraction, token accounting, and pricing logic already built for other model-driven operations.

## Recommended Follow-Up
- external IRC/websocket bridge support
- richer observer/dashboard views with live metrics panels
- role-specific bridge agents or bridge-routing policies
- opt-in integration tests for live scheduling, room switching, bridge delivery, bridge-AI generation, and streaming
