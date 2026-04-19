import re

with open('simulator_core.py', 'r') as f:
    content = f.read()

replacement = """def load_persistent_state(path: Path = STATE_FILE) -> dict[str, Any]:
    if not path.exists():
        return make_default_store()

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return make_default_store()

    state = make_default_store()
    if isinstance(payload, dict):
        if isinstance(payload.get("saved_lineups"), dict):
            state["saved_lineups"] = payload["saved_lineups"]
        if isinstance(payload.get("saved_personas"), dict):
            state["saved_personas"] = payload["saved_personas"]
        if isinstance(payload.get("saved_jobs"), dict):
            state["saved_jobs"] = payload["saved_jobs"]
        if isinstance(payload.get("saved_bridge_policies"), dict):
            state["saved_bridge_policies"] = payload["saved_bridge_policies"]
        if isinstance(payload.get("agent_specs"), dict):
            state["agent_specs"] = payload["agent_specs"]
    return state"""

content = re.sub(
    r'def load_persistent_state.*?return state',
    replacement,
    content,
    flags=re.DOTALL
)

with open('simulator_core.py', 'w') as f:
    f.write(content)
