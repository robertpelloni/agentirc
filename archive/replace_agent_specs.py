import re

with open('app.py', 'r') as f:
    content = f.read()

# Make a function to get AGENT_SPECS
get_specs_func = """
def get_agent_specs():
    return cl.user_session.get("agent_specs", {})

"""

content = re.sub(
    r'def get_config\(\) -> dict:',
    get_specs_func + 'def get_config() -> dict:',
    content
)

# Replace all occurrences of AGENT_SPECS with get_agent_specs()
content = content.replace('AGENT_SPECS', 'get_agent_specs()')

# But some places need to pass it, wait, we replaced it with get_agent_specs().
# Actually `get_agent_specs()` inside function calls will work.
# But let's check `get_agent_specs()()` because it could be `AGENT_SPECS(...)` No, AGENT_SPECS is a dict.
# Let's fix `get_agent_specs()[source]` to work correctly.

with open('app.py', 'w') as f:
    f.write(content)
