import re
with open('app.py', 'r') as f:
    content = f.read()

content = content.replace("        rebuild_team()\n    await update_settings_ui()\n        await send_system_notice", "        rebuild_team()\n        await update_settings_ui()\n        await send_system_notice")

with open('app.py', 'w') as f:
    f.write(content)
