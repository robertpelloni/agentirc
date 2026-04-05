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
- **Streaming model events are runtime-specific**, but transcript formatting, persistence, telemetry, replay, comparison, room management, and preset logic are not.
- **Helper extraction increases testability immediately** because most simulator rules can be validated without a live Chainlit or OpenRouter session.

### Result
- `app.py` focuses on Chainlit hooks, room activation, AutoGen team construction, command dispatch, scheduling, and event streaming.
- `simulator_core.py` owns the simulator’s domain behavior.

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

## 5. Prompt-Shaped Moderation Is Still a Strong Interim Control Plane
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

## 6. Hybrid Cost Tracking Is Better Than Pretending Estimates Are Truth
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

## 7. On-Demand Judging Is Still Better Than Always-On Judging
A judge is useful, but constantly inserting a judge into every simulation would add cost, latency, and noise.

### Findings
- Operators usually want evaluation after a run, not during every turn.
- A `/judge` command makes evaluation explicit and intentional.
- Keeping judge evaluation separate from the core team preserves flexibility for future upgrades like multiple judges or scoring rubrics.

## 8. Replay Changed the Meaning of Export Artifacts
Once replay mode was added, JSON exports stopped being passive archives and became active simulator assets.

### Findings
- Consistent export schema is strategically important because replay depends on it.
- Export metadata matters more because replay users need quick context about scenario, mode, topic, room, and telemetry.
- A lightweight replay surface gives immediate value without building a fully separate playback UI.

## 9. Comparison Was the Natural Next Step After Replay
Once replay existed, comparison became the next highest-value analytical operation.

### Findings
- Operators rarely want to inspect a run in isolation; they want to inspect differences between runs.
- Even a transcript-excerpt comparison is useful for spotting prompt drift, scenario changes, room differences, and conversation-shape differences.
- Comparison can be built on top of the same export artifacts and replay schema, which keeps implementation complexity low.

## 10. Bounded Scheduling Remains the Right First Automation Primitive
The simulator supports autonomous scheduled runs, but deliberately in a constrained way.

### Findings
- A bounded schedule is safer than an open-ended loop because it limits accidental runaway behavior.
- Requiring both interval and run-count intent creates a cleaner operator contract.
- Scheduling can live entirely in session state for now; it does not need persistent global orchestration yet.

## 11. Saved Jobs Are the Right Level of Automation Persistence
Saved jobs bundle simulator configuration with automation settings.

### Findings
- This captures recurring operator workflows without requiring a full scheduler or workflow engine.
- Jobs are more useful than raw interval persistence because they preserve simulation context as well as timing.
- Keeping jobs local and explicit is safer than trying to auto-restore background automation across sessions.

## 12. Room Switching Should Rebuild Runtime State, Not Preserve Live Teams
A key design choice in this pass was to rebuild the AutoGen team whenever the active room changes.

### Findings
- Persisting live team instances per room would complicate lifecycle management and background-task safety.
- Rebuilding the team on room activation is simpler, deterministic, and easier to reason about.
- This also keeps room switching compatible with room-local persona, scenario, and lineup changes.

## 13. Replay, Comparison, Rooms, and Scheduling Reinforce Each Other
These additions work best together rather than independently.

### Findings
- Rooms create parallel live experimentation contexts.
- Scheduling creates repeated outputs within a chosen context.
- Replay makes it possible to inspect those runs after export.
- Comparison makes it possible to reason about differences across runs.
- Together they move AgentIRC toward a genuine simulation-lab workflow: branch context, run experiments, export, inspect, compare, iterate.

## 14. Testing Strategy: Prioritize Helper-Layer Confidence First
The project now has stronger unit coverage around the deterministic parts of the simulator.

### Covered Areas
- command parsing
- room creation/switching/deletion
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
- automation configuration and stopping
- replay discovery and replay rendering
- replay comparison rendering
- transcript export
- persistent state round trips

### Remaining Gaps
- no live Chainlit + AutoGen integration tests yet
- no provider-backed end-to-end tests yet
- no browser automation verification yet
- schedule-loop execution has not been integration-tested against a live session
- room switching has not yet been validated in a live Chainlit integration test
- actual-cost behavior has not been verified end-to-end against provider usage metadata

## 15. Recommended Next Architecture Moves
Based on the current shape of the project, the next strongest additions would be:
1. **interactive replay stepping** rather than excerpt-only replay
2. **external IRC/websocket bridges** for non-Chainlit clients
3. **observer/dashboard views** for side-by-side run analysis
4. **cross-room summaries or bridge agents**
5. **tool-use plugins** for structured tasks inside simulations
6. **live opt-in integration tests** for streaming, judging, scheduling, and room switching
