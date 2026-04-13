import re
with open('simulator_tools.py', 'r') as f:
    content = f.read()

# Replace the broken formatted.append line
# Note: \\n becomes a literal backslash n
fixed_line = '            formatted.append(f"{i+1}. {res.get(\'title\', \'No Title\')} - {res.get(\'href\', \'No URL\')}\\n{res.get(\'body\', \'No snippet\')}")'

# Actually let's just do a string replace on the broken part
content = content.replace("formatted.append(f\"{i+1}. {res.get('title', 'No Title')} - {res.get('href', 'No URL')}\n{res.get('body', 'No snippet')}\")", fixed_line)

with open('simulator_tools.py', 'w') as f:
    f.write(content)
