import re
with open('app.py', 'r') as f:
    content = f.read()

# remove await update_settings_ui() from activate_room because it's a sync function
content = re.sub(
    r'def activate_room\(room_name: str\):.*?await update_settings_ui\(\)',
    lambda m: m.group(0).replace('await update_settings_ui()', ''),
    content,
    flags=re.DOTALL
)

with open('app.py', 'w') as f:
    f.write(content)
