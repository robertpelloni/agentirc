# Testing: Multi-Model Simulator Expansion

## Scope
Validate the helper layer that powers command parsing, room management, dashboard summaries, observer rendering, room analytics, bridge-note generation, bridge-agent prompt construction, external payload generation, inbox/outbox helpers, connector adapters, replay-window helpers, agent resolution, scenario switching, moderation controls, persona persistence, lineup persistence, job persistence, telemetry aggregation, hybrid cost tracking, judge prompt construction, replay support, replay comparison, autonomous scheduling helpers, transcript rendering, and transcript export.

## Test Commands
```bash
python -m unittest discover -s tests -v
python -m py_compile app.py run.py bridge_connectors.py bridge_runtime.py simulator_core.py tests/test_simulator_core.py tests/test_bridge_connectors.py
```

## Results
- `python -m unittest discover -s tests -v` passed on 2026-04-05
- `python -m py_compile app.py run.py bridge_connectors.py bridge_runtime.py simulator_core.py tests/test_simulator_core.py tests/test_bridge_connectors.py` passed on 2026-04-05

## Covered Behaviors
- slash-command parsing
- room create/switch/delete flow
- dashboard, observer, and room-summary helper rendering
- room analytics helper rendering
- deterministic bridge-note generation
- bridge-agent prompt generation
- external room payload generation
- external bridge payload generation
- outbox payload writing and outbox listing
- inbox payload listing and imported-payload rendering
- bridge runtime status rendering
- connector catalog rendering
- connector delivery to inbox/jsonl
- connector payload routing
- replay window resolution and replay window rendering
- agent alias and DM target resolution
- enable/disable constraints
- discuss-round validation
- moderator-mode validation
- scenario preset application
- transcript rendering
- status text generation
- persona override set/clear flow
- lineup save/load/delete flow
- job save/load/delete flow
- telemetry counters and response aggregation
- usage normalization and extraction
- cost calculation helpers
- judge prompt generation
- automation configuration and stop flow
- autonomous prompt generation
- replay listing, replay resolution, replay payload loading, replay rendering, and replay comparison rendering
- Markdown/JSON export generation
- persistent state load/save round trip

## Known Gaps
- no live integration test currently exercises Chainlit + AutoGen streaming
- no API-backed end-to-end test currently validates OpenRouter model responses
- background schedule execution is not yet integration-tested against a live Chainlit session
- room switching, bridge delivery, bridge-AI generation, external export/import, and replay stepping are not yet integration-tested with live UI runtime state
- bridge runtime processing is only compile-validated right now, not behavior-tested end-to-end
- actual cost tracking depends on provider usage metadata that is not simulated in a live end-to-end environment yet
- browser/UI verification remains manual

## Recommended Next Tests
- add mocked integration tests around command dispatch in `app.py`
- add a smoke test for loading persisted personas/lineups/jobs into a new session
- add an integration test for the schedule loop with a fake streaming team
- add a room-switch integration test validating history/config separation
- add a replay-step integration test validating cursor behavior in live session state
- add a bridge-delivery integration test validating inactive-room insertion behavior
- add a bridge-AI integration test validating model output capture and target-room insertion
- add an external-export / inbox-import integration test validating end-to-end file handoff
- add a bridge-runtime behavior test validating outbox processing into `processed/`
- add a live opt-in end-to-end test suite gated behind environment variables
