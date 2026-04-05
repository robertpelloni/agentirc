# Testing: Multi-Model Simulator Expansion

## Scope
Validate the helper layer that powers command parsing, agent resolution, scenario switching, moderation controls, persona persistence, lineup persistence, telemetry aggregation, judge prompt construction, replay support, autonomous scheduling helpers, transcript rendering, and transcript export.

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
- agent alias and DM target resolution
- enable/disable constraints
- discuss-round validation
- moderator-mode validation
- scenario preset application
- transcript rendering
- status text generation
- persona override set/clear flow
- lineup save/load/delete flow
- telemetry counters and response aggregation
- judge prompt generation
- automation configuration and stop flow
- autonomous prompt generation
- replay listing, replay resolution, replay payload loading, and replay rendering
- Markdown/JSON export generation
- persistent state load/save round trip

## Known Gaps
- no live integration test currently exercises Chainlit + AutoGen streaming
- no API-backed end-to-end test currently validates OpenRouter model responses
- background schedule execution is not yet integration-tested against a live Chainlit session
- `/judge` behavior is only structurally tested at the prompt-construction layer
- browser/UI verification remains manual

## Recommended Next Tests
- add mocked integration tests around command dispatch in `app.py`
- add a smoke test for loading persisted personas/lineups into a new session
- add an integration test for the schedule loop with a fake streaming team
- add a live opt-in end-to-end test suite gated behind environment variables
