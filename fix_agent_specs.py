import re

with open('app.py', 'r') as f:
    content = f.read()

content = content.replace("rooms = make_initial_rooms(get_agent_specs()", "rooms = make_initial_rooms(agent_specs")
content = content.replace("agent_specs = persistent_state.get(\"agent_specs\", {})", "agent_specs = persistent_state.get(\"agent_specs\", {})")

with open('app.py', 'w') as f:
    f.write(content)
