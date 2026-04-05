# Testing: Multi-Model Simulator Expansion

## Scope
Validate the helper layer that powers command parsing, room management, agent resolution, scenario switching, moderation controls, persona persistence, lineup persistence, job persistence, telemetry aggregation, hybrid cost tracking, judge prompt construction, replay support, replay comparison, autonomous scheduling helpers, transcript rendering, and transcript export.

## Test Commands
```bash
python -m unittest discover -s tests -v
python -m py_compile app.py run.py simulator_core.py tests/test_simulator_core.py
```

## Results
- `python -m unittest discover -s tests -v` passed on 2026-04-05
- `python -m py_compile app.py run.py simulator_core.py tests/test_simulator_core.py` passed on 2026-04-05

## Covered Behaviors
- slash-command parsing
- room create/switch/delete flow
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
- room switching is only unit-tested at the helper layer, not with live UI runtime state
- actual cost tracking depends on provider usage metadata that is not simulated in a live end-to-end environment yet
- browser/UI verification remains manual

## Recommended Next Tests
- add mocked integration tests around command dispatch in `app.py`
- add a smoke test for loading persisted personas/lineups/jobs into a new session
- add an integration test for the schedule loop with a fake streaming team
- add a room-switch integration test validating history/config separation
- add a live opt-in end-to-end test suite gated behind environment variables
