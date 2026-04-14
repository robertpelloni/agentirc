import re

with open('app.py', 'r') as f:
    content = f.read()

settings_code = """
from chainlit.input_widget import Select, TextInput, Switch

async def update_settings_ui():
    agent_specs = get_agent_specs()
    config = get_config()

    widgets = [
        TextInput(
            id="topic",
            label="Room Topic",
            initial=config.get("topic", "")
        )
    ]

    for agent_name in agent_specs.keys():
        widgets.append(
            Switch(
                id=f"agent_{agent_name}",
                label=f"Enable {agent_name}",
                initial=agent_name in config["enabled_agents"]
            )
        )

    settings = await cl.ChatSettings(widgets).send()

@cl.on_settings_update
async def setup_agent(settings):
    config = get_config()
    agent_specs = get_agent_specs()
    changed = False

    if "topic" in settings and settings["topic"] != config["topic"]:
        config["topic"] = settings["topic"]
        await send_system_notice(f"Topic changed to: {config['topic']}")
        changed = True

    enabled_agents = []
    for agent_name in agent_specs.keys():
        key = f"agent_{agent_name}"
        if key in settings and settings[key]:
            enabled_agents.append(agent_name)

    if set(enabled_agents) != set(config["enabled_agents"]):
        config["enabled_agents"] = enabled_agents
        changed = True

    if changed:
        rebuild_team()
        save_current_room_state()
"""

# Insert chat settings definition
content = re.sub(
    r'@cl\.on_chat_start',
    settings_code + '\n@cl.on_chat_start',
    content
)

# Call update_settings_ui() inside start()
content = re.sub(
    r'rebuild_team\(\)',
    'rebuild_team()\n    await update_settings_ui()',
    content
)

with open('app.py', 'w') as f:
    f.write(content)
