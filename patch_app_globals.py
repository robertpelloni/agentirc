import re

with open('app.py', 'r') as f:
    content = f.read()

# Remove the global AGENT_SPECS definition in app.py
content = re.sub(
    r'AGENT_SPECS = \{.*?\n\}\n\n',
    '\n',
    content,
    flags=re.DOTALL
)

# Use dynamic AGENT_SPECS from persistent state inside app.py
# First replace the global `AGENT_SPECS` references in top-level functions to get it from persistent state
replacement_start = """
@cl.on_chat_start
async def start():
    persistent_state = load_persistent_state(STATE_FILE)
    cl.user_session.set(SESSION_STATE_KEY, persistent_state)
    agent_specs = persistent_state.get("agent_specs", {})
    cl.user_session.set("agent_specs", agent_specs)

    rooms = make_initial_rooms(agent_specs, persistent_state)
"""

content = re.sub(
    r'@cl\.on_chat_start\nasync def start\(\):\n    persistent_state = load_persistent_state\(STATE_FILE\)\n    cl\.user_session\.set\(SESSION_STATE_KEY, persistent_state\)\n    rooms = make_initial_rooms\(AGENT_SPECS, persistent_state\)',
    replacement_start.strip(),
    content
)

with open('app.py', 'w') as f:
    f.write(content)
