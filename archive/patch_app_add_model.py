import re

with open('app.py', 'r') as f:
    content = f.read()

replacement = """    if command == "/add-model":
        parts = args.split(" ", 2)
        if len(parts) < 2:
            await send_system_notice("Usage: `/add-model <Name> <provider/model-id> [Bio]`")
            return True
        name = parts[0]
        model_id = parts[1]
        bio = parts[2] if len(parts) > 2 else "A new agent."

        agent_specs = get_agent_specs()
        agent_specs[name] = {
            "model": model_id,
            "color": "#cccccc",
            "bio": bio,
            "pricing": {"input_per_million": 0.0, "output_per_million": 0.0}
        }
        persistent_state = get_persistent_state()
        persistent_state["agent_specs"] = agent_specs
        persist_state()
        await update_settings_ui()
        await send_system_notice(f"Added new model '{name}' mapping to `{model_id}`.")
        return True"""

content = re.sub(
    r'    if command == "/enable-tool":',
    replacement + '\n\n    if command == "/enable-tool":',
    content
)

with open('app.py', 'w') as f:
    f.write(content)
