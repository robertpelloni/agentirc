# AgentIRC Technical Findings & Analysis

## 1. Python 3.14.3 Runtime Hardening
Operating on the experimental Python 3.14.3 runtime continues to expose breaking changes in `asyncio` and `anyio` assumptions used by Chainlit and related libraries.

### Findings
- **Strict Task Context**: Python 3.14 more aggressively enforces valid `asyncio.Task` state for timeout and cancellation flows.
- **Background Loop Mismatch**: `engineio` / Chainlit paths still assume looser task semantics than Python 3.14 currently tolerates.
- **Weakref Sensitivity**: `anyio` cancellation machinery is brittle when task identity is absent or malformed.

### Current Approach
- `run.py` applies broad compatibility shims to preserve startup.
- `app.py` also patches `anyio.to_thread.run_sync` so sync-to-thread behavior remains usable inside the app runtime.
- We preserved process safety and did not terminate any background processes while working in this environment.

## 2. AutoGen Modular Architecture Works Best with Explicit Boundaries
The simulator became significantly easier to extend after splitting general-purpose simulator logic out of `app.py`.

### Findings
- **Live UI code and reusable domain logic should not live in the same file** once command surface area grows.
- **Streaming model events are runtime-specific**, but transcript formatting, persistence, telemetry, replay, comparison, room management, dashboard rendering, bridge-note generation, observer views, external payload generation, inbox/outbox handling, connector adaptation, and preset logic are not.
- **Helper extraction increases testability immediately** because most simulator rules can be validated without a live Chainlit or OpenRouter session.

### Result
- `app.py` focuses on Chainlit hooks, room activation, replay state, AutoGen team construction, command dispatch, scheduling, and event streaming.
- `simulator_core.py` owns the simulator’s domain behavior.
- `bridge_runtime.py` is now the first standalone runtime scaffold dedicated to external bridge processing.
- `bridge_connectors.py` is the adapter layer between payload processing and future live transports.

## 3. Stateful Operator Features Continue to Deliver Outsized Value
The highest-leverage additions were not new models but operator workflow improvements.

### Findings
- Re-entering personas, lineups, recurring automation settings, and alternate simulation contexts every session creates friction and slows experimentation.
- Durable presets make the simulator feel like a real operations console rather than a toy chat room.
- A small local state file plus session-local rooms is enough to unlock repeatable workflows without overengineering the persistence layer.

### Implemented Capabilities
- persistent persona overrides
- saved lineups
- saved jobs
- room-local live state
- dashboard-style session summaries
- observer ranking views
- richer status inspection

## 4. Session Rooms Are the Right First Form of Multi-Channel Support
Multi-room support was the next logical step after replay, jobs, and comparison.

### Findings
- Operators need to run parallel contexts like `lobby`, `war-room`, `benchmark`, or `redteam` without destroying the current conversation state.
- Session-scoped rooms provide most of the value of channels without forcing a persistent multi-user architecture too early.
- Room-local config/history separation is more important than room persistence at this stage.

### Current Room Model
- `/rooms` lists rooms
- `/room [name]` shows or switches rooms
- `/new-room <name>` creates and switches to a room
- `/delete-room <name>` removes a room and falls back safely when required
- each room has its own config and transcript history

## 5. Dashboard and Observer Views Became Necessary Once Rooms Existed
As soon as the simulator gained multiple live contexts, operators needed fast global visibility.

### Findings
- A room list alone is not enough once rooms accumulate their own histories and costs.
- A dashboard gives the operator a control-tower summary.
- An observer view adds ranking and prioritization, which becomes useful when several rooms are active at once.
- Text-first operational views remain surprisingly effective for a command-driven simulator and avoid needing immediate UI redesign.

### Current Visibility Model
- `/dashboard` gives a top-level summary across rooms, jobs, active context, aggregate prompts, bridge activity, external import/export activity, and aggregate estimated cost
- `/observer` provides a ranked multi-room operational view
- `/room-summary [count]` previews recent activity across rooms
- `/room-analytics [name]` drills into one room’s local metrics and analytics

## 6. Prompt-Shaped Moderation Is Still a Strong Interim Control Plane
Instead of adding a separate moderator agent immediately, we injected moderation rules into each agent’s system prompt.

### Findings
- This gives operators useful control over tone and discipline at much lower complexity.
- It avoids another active speaker competing for turns in every simulation.
- It keeps costs lower and preserves clearer causal reasoning about why a response changed.

### Implemented Modes
- `off`
- `facilitator`
- `strict`
- `critic`
- `chaos`

## 7. Hybrid Cost Tracking Is Better Than Pretending Estimates Are Truth
True provider billing data is not guaranteed across all backends, but the simulator can still provide useful cost observability.

### Findings
- Some streamed events may expose usage metadata; others may not.
- Treating all token counts as "real" would create false precision.
- A hybrid model is more honest and more useful:
  - use provider usage when available
  - fall back to estimates when it is not
- Pricing hints attached to agent definitions create an operator-tunable cost model rather than hard-coding invisible assumptions.

### Important Caveat
Even the "actual" cost view is only as reliable as the provider usage data surfaced through the event stream.

## 8. On-Demand Judging Is Still Better Than Always-On Judging
A judge is useful, but constantly inserting a judge into every simulation would add cost, latency, and noise.

### Findings
- Operators usually want evaluation after a run, not during every turn.
- A `/judge` command makes evaluation explicit and intentional.
- Keeping judge evaluation separate from the core team preserves flexibility for future upgrades like multiple judges or scoring rubrics.

## 9. Replay Changed the Meaning of Export Artifacts
Once replay mode was added, JSON exports stopped being passive archives and became active simulator assets.

### Findings
- Consistent export schema is strategically important because replay depends on it.
- Export metadata matters more because replay users need quick context about scenario, mode, topic, room, and telemetry.
- A lightweight replay surface gives immediate value without building a fully separate playback UI.

## 10. Cursor-Based Replay Stepping Is the Right Lightweight Replay Model
Interactive replay stepping was the next step after basic replay and comparison.

### Findings
- A cursor-based replay window gives real navigation without needing a heavy playback engine.
- Operators can step, rewind, jump to the start/end, or jump to a specific index with a simple state model.
- Keeping the replay state in session memory aligns well with the command-driven interaction style.

### Current Replay-Step Model
- `/replay-open [latest|previous|file.json] [count]`
- `/replay-step [next|prev|start|end|index] [count]`
- replay cursor state lives in session state rather than persistent storage

## 11. Comparison Was the Natural Next Step After Replay
Once replay existed, comparison became the next highest-value analytical operation.

### Findings
- Operators rarely want to inspect a run in isolation; they want to inspect differences between runs.
- Even a transcript-excerpt comparison is useful for spotting prompt drift, scenario changes, room differences, and conversation-shape differences.
- Comparison can be built on top of the same export artifacts and replay schema, which keeps implementation complexity low.

## 12. Deterministic Bridge Notes Are the Right First Cross-Room Primitive
Bridge notes were the next practical feature after multi-room state and dashboards.

### Findings
- Operators need a lightweight way to transfer context from one room into another.
- Deterministic bridge notes are cheap, predictable, and easy to validate.
- Model-generated bridge agents can come later, once operators prove they need abstraction instead of literal context transfer.

### Current Bridge Model
- `/bridge <source> <target> [count]`
- uses recent transcript lines from the source room
- inserts a room-local system note into the target room
- increments bridge telemetry on the target room

## 13. Model-Generated Bridge Notes Are the Right Next Step After Deterministic Bridges
After deterministic bridges, the next useful feature is a smarter summarization mode.

### Findings
- Some operators want high-fidelity literal context transfer; others want a distilled operational summary.
- A dedicated bridge agent provides that higher abstraction without changing the underlying room model.
- Reusing the judge model for the bridge agent keeps the architecture small while still adding real capability.
- Bridge-agent generation fits naturally into the existing telemetry and cost-accounting model.

### Current Bridge-AI Model
- `/bridge-ai <source> <target> [focus]`
- uses a bridge-agent prompt built from recent source-room history
- delivers the model-generated note into the target room
- tracks bridge-AI events, costs, and usage when available

## 14. External Connectors Should Evolve in Layers: Payloads, Runtime Scaffold, Connector Adapters, Then Live Transports
The next natural step after bridge agents is preparing stable external integration boundaries and a minimal processing runtime.

### Findings
- A file-based outbox/inbox/processed flow is safer and easier to validate than immediately embedding live websocket or IRC infrastructure.
- Connector payload schemas matter more early than transport details.
- A standalone runtime scaffold creates an operational place for future transport adapters without bloating the main app.
- A connector adapter layer is the right seam between file-based routing and future live runtimes.
- Once payloads, routing, and runtime flow are stable, multiple future transports can be added with less risk.

### Current External Foundation Model
- `/bridge-export <room> [count]`
- `/bridge-runtime`
- `/connectors`
- `/outbox`
- `/inbox`
- `/import-bridge <file> [room]`
- standardized `room_snapshot` payloads
- standardized `bridge_note` payload helpers
- connector adapters for `console`, `inbox`, and `jsonl`
- JSON payloads written into `outbox/`
- inbound payloads read from `inbox/`
- processed payloads moved into `processed/`
- `bridge_runtime.py` for one-shot or polling processing
- `bridge_connectors.py` for connector-level routing

## 15. Bounded Scheduling Remains the Right First Automation Primitive
The simulator supports autonomous scheduled runs, but deliberately in a constrained way.

### Findings
- A bounded schedule is safer than an open-ended loop because it limits accidental runaway behavior.
- Requiring both interval and run-count intent creates a cleaner operator contract.
- Scheduling can live entirely in session state for now; it does not need persistent global orchestration yet.

## 16. Saved Jobs Are the Right Level of Automation Persistence
Saved jobs bundle simulator configuration with automation settings.

### Findings
- This captures recurring operator workflows without requiring a full scheduler or workflow engine.
- Jobs are more useful than raw interval persistence because they preserve simulation context as well as timing.
- Keeping jobs local and explicit is safer than trying to auto-restore background automation across sessions.

## 17. Room Switching Should Rebuild Runtime State, Not Preserve Live Teams
A key design choice in this pass was to rebuild the AutoGen team whenever the active room changes.

### Findings
- Persisting live team instances per room would complicate lifecycle management and background-task safety.
- Rebuilding the team on room activation is simpler, deterministic, and easier to reason about.
- This also keeps room switching compatible with room-local persona, scenario, and lineup changes.

## 18. Replay, Comparison, Rooms, Dashboards, Bridge Notes, Bridge Agents, External Payloads, Runtime Scaffolding, Connector Adapters, and Scheduling Reinforce Each Other
These additions work best together rather than independently.

### Findings
- Rooms create parallel live experimentation contexts.
- Scheduling creates repeated outputs within a chosen context.
- Replay makes it possible to inspect those runs after export.
- Replay stepping improves the precision of that inspection.
- Comparison makes it possible to reason about differences across runs.
- Dashboard and observer views make it possible to monitor the whole session at a glance.
- Deterministic bridge notes make it possible to transfer literal context between experiments.
- Bridge agents make it possible to transfer distilled context between experiments.
- External payloads create a clean handoff surface for future connectors.
- Runtime scaffolding provides the first operational processing loop outside the main UI app.
- Connector adapters create the seam that future live transports can plug into.
- Together they move AgentIRC toward a genuine simulation-lab workflow: branch context, run experiments, export, inspect, compare, monitor, bridge, summarize, hand off, route, process, iterate.

## 19. Testing Strategy: Prioritize Helper-Layer Confidence First
The project now has stronger unit coverage around the deterministic parts of the simulator.

### Covered Areas
- command parsing
- room creation/switching/deletion
- dashboard, observer, and room-summary rendering
- room analytics rendering
- alias resolution
- scenario switching
- moderator mode validation
- persona persistence logic
- lineup persistence logic
- job persistence logic
- telemetry aggregation
- usage normalization and extraction
- cost calculation helpers
- judge prompt construction
- bridge-note generation
- bridge-agent prompt generation
- external payload generation
- outbox writing and listing
- inbox listing and imported-payload rendering
- connector catalog rendering
- connector payload routing
- automation configuration and stopping
- replay discovery and replay rendering
- replay window resolution and replay-window rendering
- replay comparison rendering
- transcript export
- persistent state round trips

### Remaining Gaps
- no live Chainlit + AutoGen integration tests yet
- no provider-backed end-to-end tests yet
- no browser automation verification yet
- schedule-loop execution has not been integration-tested against a live session
- room switching has not yet been validated in a live Chainlit integration test
- bridge delivery has not yet been validated in a live Chainlit integration test
- bridge-AI delivery has not yet been validated in a live Chainlit integration test
- external export/import command flow has not yet been validated in a live Chainlit integration test
- bridge runtime processing is not yet behavior-tested end-to-end
- actual-cost behavior has not been verified end-to-end against provider usage metadata
- replay cursor behavior is not yet integration-tested in a live session loop

## 20. Auto-Bridge Policies Are the Right Follow-On to Manual Bridge Workflows
Manual room-to-room bridges are useful, but still depend on operator attention.

### Findings
- Prompt-count-based auto-bridges are a safe first automation model because they piggyback on already-observed activity rather than requiring timers or background daemons.
- Supporting both `note` and `ai` modes preserves the same quality/cost tradeoff used elsewhere in the bridge system.
- Auto-bridge turns the simulator from a reactive system into a more policy-driven one.

## 21. Room Archives Are the Right First Persistence Primitive for Live Room State
Persisting every room automatically would be premature. Explicit archives are a better first step.

### Findings
- Archives preserve a scenario snapshot without forcing a full persistent multi-room database design.
- Restore operations are easier to reason about than implicit session resurrection.
- Operators can now branch, archive, restore, and compare room states as deliberate workflows.

## 22. Saved Auto-Bridge Policies Are the Right Follow-On to Auto-Bridge Itself
Once prompt-interval bridge automation exists, operators quickly need repeatable presets.

### Findings
- Saving auto-bridge policies removes repeated manual configuration for common room-routing workflows.
- Policies belong in the same persistence layer as saved jobs and saved lineups because they are reusable operator assets rather than volatile runtime state.
- Loading a bridge policy is a safer first step than inventing a full bridge automation orchestration engine.

## 23. A Standard-Library IRC Runtime Is the Right First Live Transport Experiment
The next practical step after the connector layer is a transport-specific scaffold that still avoids extra dependencies.

### Findings
- A standard-library IRC runtime proves the transport direction while keeping the dependency footprint small.
- IRC is a natural fit for this project’s interaction model and helps validate how exported room payloads map to line-oriented network messages.
- A transport-specific scaffold is a cleaner next step than jumping straight to a full multiplexed connector service.

## 24. Live Integration Tests Must Stay Opt-In
Provider-backed and network-backed tests are useful, but dangerous if they run by default.

### Findings
- Environment-gated live tests are the right compromise between realism and safety.
- A skipped-by-default live suite communicates intended future test coverage without surprising local or CI runs.
- It is better to scaffold live tests clearly now than to leave external/runtime validation completely undocumented.

## 25. Recommended Next Architecture Moves
Based on the current shape of the project, the next strongest additions would be:
1. **external websocket bridge runtime** for non-Chainlit clients on top of the connector layer
2. **richer observer/dashboard views with live metrics panels**
3. **role-specific bridge agents** or bridge-routing policies
4. **tool-use plugins** for structured tasks inside simulations
5. **deeper live opt-in integration tests** for streaming, judging, scheduling, room switching, bridge delivery, bridge-AI generation, external export/import, auto-bridge execution, and replay stepping
6. **persistent archived room snapshots** across restarts
