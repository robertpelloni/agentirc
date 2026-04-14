import re

with open('app.py', 'r') as f:
    content = f.read()

replacement = """    if command == "/topic":
        if not args:
            await send_system_notice(f"Current topic: {config['topic']}")
            return True
        config["topic"] = args
        await update_settings_ui()
        await send_system_notice(f"Topic changed to: {args}")
        return True"""

content = re.sub(
    r'    if command == "/topic":.*?return True',
    replacement,
    content,
    flags=re.DOTALL
)

with open('app.py', 'w') as f:
    f.write(content)
