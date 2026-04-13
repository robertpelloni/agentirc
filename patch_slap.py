import re
with open('app.py', 'r') as f:
    content = f.read()

replacement = """    if command == "/help":
        await cl.Message(content=build_help_text()).send()
        return True

    if command == "/slap":
        target = args if args else "someone"
        content = f"* {config['nick']} slaps {target} around a bit with a large trout"
        add_history_entry(author="system", content=content, kind="system")
        await cl.Message(author="system", content=content).send()
        # Feed it to the models
        await stream_agent(
            cl.user_session.get(SESSION_TEAM_KEY),
            content,
            telemetry_name="system"
        )
        return True

    if command == "/me":
        content = f"* {config['nick']} {args}"
        add_history_entry(author="system", content=content, kind="system")
        await cl.Message(author="system", content=content).send()
        # Feed it to the models
        await stream_agent(
            cl.user_session.get(SESSION_TEAM_KEY),
            content,
            telemetry_name="system"
        )
        return True"""

content = re.sub(
    r'    if command == "/help":\n        await cl\.Message\(content=build_help_text\(\)\)\.send\(\)\n        return True',
    replacement,
    content
)

with open('app.py', 'w') as f:
    f.write(content)
