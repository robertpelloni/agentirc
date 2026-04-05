# Simulator Operations Design

## Objective
Evolve AgentIRC from a simple multi-model chat room into a reusable simulation platform with configurable orchestration, durable operator presets, autonomous scheduling, replayable analytical artifacts, hybrid cost tracking, reusable autonomous jobs, room-scoped simulation workflows, operator dashboard tools, and cross-room context sharing.

## Architecture Summary
The simulator now separates into eight distinct concerns:
1. **UI and runtime orchestration** in `app.py`
2. **Pure helper/domain logic** in `simulator_core.py`
3. **Session room registry** in Chainlit session state
4. **Replay cursor state** in Chainlit session state
5. **Persistent operator state** in `data/simulator_state.json`
6. **Exported analytical artifacts** in `exports/`
7. **In-session autonomous scheduling** managed by a background asyncio task handle in Chainlit session state
8. **Hybrid telemetry and cost accounting** derived from provider usage data where available and heuristics otherwise

## Design Decisions
### 1. Rooms are session-scoped, not globally persisted
Rooms represent alternate simulation contexts inside one live operator session. They keep:
- room-local config
- room-local transcript history

Rooms do **not** persist across full application restarts yet. This keeps the model simple and avoids conflating operator presets with live chat state.

### 2. Replay stepping should be cursor-based, not a separate playback engine
Interactive replay stepping is implemented as a lightweight replay-window cursor held in session state.

This approach:
- reuses existing export artifacts
- avoids introducing a complex playback subsystem
- keeps the model textual and command-driven
- lets operators jump, step, rewind, and inspect replay windows incrementally

### 3. Dashboards should be summary-first, not UI-heavy
The operator dashboard, observer view, and room-summary surfaces are intentionally text-first.

This approach:
- keeps implementation cost low
- fits the IRC/control-console aesthetic
- provides value before a custom visual dashboard exists
- remains easy to test at the helper layer

### 4. Cross-room bridges have two modes: deterministic and model-generated
The simulator now supports two bridge styles:
- **deterministic bridge note**: low-cost, predictable context transfer from recent transcript lines
- **model-generated bridge note**: higher-level abstraction using a bridge agent prompt

This dual approach gives operators a practical cost/quality tradeoff.

### 5. Keep persistence small and explicit
Persistent state currently stores:
- saved lineups
- saved persona overrides
- saved jobs

This preserves high-value reusable operator assets without persisting volatile room histories or live automation state.

### 6. Use hybrid cost tracking instead of pretending heuristics are truth
The simulator attempts to read model usage metadata from events when available. If provider-native usage is missing, it falls back to estimated token counts based on text length.

This creates a layered model:
- **actual cost** when usage metadata exists and pricing hints are configured
- **estimated cost** otherwise

### 7. Make autonomous scheduling opt-in and bounded
The schedule system is configured explicitly through `/schedule` or `/run-job`. Each scheduled run is bounded by a configured run count and interval. This reduces the risk of runaway autonomous activity while still enabling repeated unattended simulations.

### 8. Room switching rebuilds active runtime state
When the operator switches rooms, the app swaps in the selected room’s config and history, then rebuilds the active AutoGen team. This preserves room-local behavior without duplicating long-lived model runtime objects per room.

## Flow Diagram
```mermaid
flowchart TD
    User[User prompt or slash command] --> CL[Chainlit handlers in app.py]
    CL --> Cmd{Command?}
    Cmd -- Yes --> Core[simulator_core.py helper logic]
    Core --> Rooms[Room registry in session state]
    Core --> ReplayState[Replay cursor state]
    Core --> Persist{Persistent change?}
    Persist -- Yes --> State[data/simulator_state.json]
    Persist -- No --> Session[Active room config + history + telemetry]
    Cmd -- Dashboard --> Rooms
    Cmd -- Observer --> Rooms
    Cmd -- Room Summary --> Rooms
    Cmd -- Bridge --> Rooms
    Cmd -- Bridge AI --> BridgeAgent[Bridge Agent]
    Cmd -- Replay --> Exports[exports/*.json replay artifacts]
    Cmd -- Replay Step --> ReplayState
    Cmd -- Compare --> Exports
    Cmd -- Schedule --> Task[Async automation task]
    Cmd -- Run Job --> Jobs[Saved jobs]
    Cmd -- Judge --> Judge[Dedicated judge agent]
    Cmd -- No --> Team[AutoGen team or single agent]
    Rooms --> Team
    Jobs --> Task
    Task --> Team
    Team --> Stream[Stream responses back to Chainlit]
    Judge --> Stream
    BridgeAgent --> Stream
    Stream --> Usage[Usage metadata when available]
    Usage --> Telemetry[Update telemetry + cost tracking]
    Telemetry --> History[Append active room transcript history]
    History --> Export[Optional export to Markdown/JSON]
```

## Data Model Highlights
### Active Room State
- room name
- room-local config
- room-local history

### Replay Cursor State
- replay file name
- replay payload
- current window start index
- current window size

### Session Config
- room name
- mode
- topic
- nick
- scenario
- max rounds
- moderator mode
- judge model
- enabled agents
- persona overrides
- simulation count
- telemetry
- automation state

### Persistent State
- `saved_lineups`
- `saved_personas`
- `saved_jobs`

### Transcript Entry
- timestamp
- author
- content
- kind
- target

### Automation State
- enabled
- interval seconds
- remaining runs
- total run limit
- active job name
- last run timestamp
- next run timestamp

### Per-Agent Telemetry
- messages
- chars
- prompt tokens
- completion tokens
- total tokens
- estimated cost
- actual cost
- usage sample count
- average latency
- bridge events
- bridge ai events
- observer views

## Tradeoffs
### Pros
- room separation enables parallel what-if contexts inside one session
- replay stepping adds operator control without a heavy playback subsystem
- dashboard and observer commands provide immediate control-tower value
- deterministic and model-generated bridge modes give a useful quality/cost tradeoff
- persistence footprint stays small
- autonomous runs are bounded and explicit

### Cons
- rooms are not yet persisted across application restarts
- bridge AI depends on live model availability and cost
- autonomous scheduling still depends on live Chainlit runtime behavior
- actual cost depends on provider usage metadata being present
- replay mode is still textual rather than visual/graphical
- saved jobs are local-file based, not multi-user shared

## Recommended Future Extensions
- add external IRC/websocket bridges and richer observer dashboards
- add role-specific bridge agents or bridge-routing policies
- add provider-backed live integration tests behind environment flags
- add persistent archived room snapshots when session-level room history becomes strategically valuable
- add visual dashboard panels if the command-first interface stops being sufficient
