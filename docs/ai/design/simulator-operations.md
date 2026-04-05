# Simulator Operations Design

## Objective
Evolve AgentIRC from a simple multi-model chat room into a reusable simulation platform with configurable orchestration, durable operator presets, autonomous scheduling, replayable analytical artifacts, hybrid cost tracking, reusable autonomous jobs, and room-scoped simulation workflows.

## Architecture Summary
The simulator now separates into seven distinct concerns:
1. **UI and runtime orchestration** in `app.py`
2. **Pure helper/domain logic** in `simulator_core.py`
3. **Session room registry** in Chainlit session state
4. **Persistent operator state** in `data/simulator_state.json`
5. **Exported analytical artifacts** in `exports/`
6. **In-session autonomous scheduling** managed by a background asyncio task handle in Chainlit session state
7. **Hybrid telemetry and cost accounting** derived from provider usage data where available and heuristics otherwise

## Design Decisions
### 1. Rooms are session-scoped, not globally persisted
Rooms represent alternate simulation contexts inside one live operator session. They keep:
- room-local config
- room-local transcript history

Rooms do **not** persist across full application restarts yet. This keeps the model simple and avoids conflating operator presets with live chat state.

### 2. Keep persistence small and explicit
Persistent state currently stores:
- saved lineups
- saved persona overrides
- saved jobs

This preserves high-value reusable operator assets without persisting volatile room histories or live automation state.

### 3. Use hybrid cost tracking instead of pretending heuristics are truth
The simulator attempts to read model usage metadata from events when available. If provider-native usage is missing, it falls back to estimated token counts based on text length.

This creates a layered model:
- **actual cost** when usage metadata exists and pricing hints are configured
- **estimated cost** otherwise

### 4. Make autonomous scheduling opt-in and bounded
The schedule system is configured explicitly through `/schedule` or `/run-job`. Each scheduled run is bounded by a configured run count and interval. This reduces the risk of runaway autonomous activity while still enabling repeated unattended simulations.

### 5. Prefer replay and comparison from export artifacts over live transcript mutation
Replay mode and comparison mode read exported JSON transcript snapshots rather than mutating the live transcript state. This keeps replay analysis separate from active-session simulation and preserves a clean operational model.

### 6. Persist reusable jobs instead of inventing a job server
Saved jobs are local presets that bundle schedule parameters with simulation state. This captures high-value operator workflows without requiring a full distributed scheduler.

### 7. Room switching rebuilds active runtime state
When the operator switches rooms, the app swaps in the selected room’s config and history, then rebuilds the active AutoGen team. This preserves room-local behavior without duplicating long-lived model runtime objects per room.

## Flow Diagram
```mermaid
flowchart TD
    User[User prompt or slash command] --> CL[Chainlit handlers in app.py]
    CL --> Cmd{Command?}
    Cmd -- Yes --> Core[simulator_core.py helper logic]
    Core --> Rooms[Room registry in session state]
    Core --> Persist{Persistent change?}
    Persist -- Yes --> State[data/simulator_state.json]
    Persist -- No --> Session[Active room config + history + telemetry]
    Cmd -- Replay --> Exports[exports/*.json replay artifacts]
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

## Tradeoffs
### Pros
- room separation enables parallel what-if contexts inside one session
- persistence footprint stays small
- autonomous runs are bounded and explicit
- replay/compare mode leverages existing export artifacts
- cost tracking is useful even when only partially backed by provider metadata

### Cons
- rooms are not yet persisted across application restarts
- autonomous scheduling still depends on live Chainlit runtime behavior
- actual cost depends on provider usage metadata being present
- replay mode currently renders transcript excerpts rather than interactive step playback
- saved jobs are local-file based, not multi-user shared

## Recommended Future Extensions
- add interactive replay navigation with seek/step controls
- add multiple channels with room-to-room summaries or bridge agents
- add external IRC/websocket bridges and observer dashboards
- add provider-backed live integration tests behind environment flags
- add persistent archived room snapshots when session-level room history becomes strategically valuable
