import re
with open('app.py', 'r') as f:
    content = f.read()

content = content.replace("        rebuild_team()\n    await update_settings_ui()\n            await stop_automation_task()", "        rebuild_team()\n        await update_settings_ui()\n        await stop_automation_task()")

with open('app.py', 'w') as f:
    f.write(content)
