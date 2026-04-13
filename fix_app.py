import re
with open('app.py', 'r') as f:
    content = f.read()

content = content.replace("def rebuild_team()\n    await update_settings_ui():\n    config = get_config()", "def rebuild_team():\n    config = get_config()")
with open('app.py', 'w') as f:
    f.write(content)
