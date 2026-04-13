import re
with open('app.py', 'r') as f:
    content = f.read()

content = content.replace("    rebuild_team()\n    await update_settings_ui()\n\n\n\ndef append_entry_to_room", "    rebuild_team()\n\n\n\ndef append_entry_to_room")
content = content.replace("async def update_settings_ui():", "async def update_settings_ui():")

# Wait, `activate_room` is sync, it cannot call `await update_settings_ui()`.
# Let's see if there are other `await update_settings_ui()` in sync functions.

content = content.replace("def rebuild_team():\n    config = get_config()\n    team = create_team(config)\n    cl.user_session.set(SESSION_TEAM_KEY, team)\n    return team\n", "def rebuild_team():\n    config = get_config()\n    team = create_team(config)\n    cl.user_session.set(SESSION_TEAM_KEY, team)\n    return team\n")

with open('app.py', 'w') as f:
    f.write(content)
