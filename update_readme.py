import re
with open('README.md', 'r') as f:
    content = f.read()

# Make sure VERSION is somewhat referenced in README
content = re.sub(r'# AgentIRC: The Multi-Model Broadcast Network', '# AgentIRC: The Multi-Model Broadcast Network (v1.1.0)', content)

with open('README.md', 'w') as f:
    f.write(content)
