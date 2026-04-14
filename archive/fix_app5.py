import re
with open('app.py', 'r') as f:
    content = f.read()

content = content.replace("    if changed:\n        rebuild_team()\n    await update_settings_ui()\n        save_current_room_state()", "    if changed:\n        rebuild_team()\n        await update_settings_ui()\n        save_current_room_state()")

with open('app.py', 'w') as f:
    f.write(content)
