import re

with open('app.py', 'r') as f:
    content = f.read()

replacement = """    if command in {"/enable", "/disable"}:
        if not args:
            await send_system_notice(f"Usage: `{command} <agent>`")
            return True
        changed, response = set_agent_enabled(
            config=config,
            raw_name=args,
            enabled=command == "/enable",
            agent_specs=get_agent_specs(),
        )
        if changed:
            rebuild_team()
            await update_settings_ui()
        await send_system_notice(response)
        return True"""

content = re.sub(
    r'    if command in \{"/enable", "/disable"\}:.*?return True',
    replacement,
    content,
    flags=re.DOTALL
)

with open('app.py', 'w') as f:
    f.write(content)
