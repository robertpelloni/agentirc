import re
with open('app.py', 'r') as f:
    content = f.read()

content = content.replace("        await update_settings_ui()\n        await stop_automation_task()\n            task = asyncio.create_task(run_automation_loop())\n            set_automation_task(task)\n", "            await update_settings_ui()\n            await stop_automation_task()\n            task = asyncio.create_task(run_automation_loop())\n            set_automation_task(task)\n")

with open('app.py', 'w') as f:
    f.write(content)
