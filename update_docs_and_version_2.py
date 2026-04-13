import re
import os

# Update TODO.md checkbox
with open('TODO.md', 'r') as f:
    todo_content = f.read()
todo_content = todo_content.replace(
    '- [ ] Further polish the 1990s IRC interface look and feel with terminal-style sounds.',
    '- [x] Further polish the 1990s IRC interface look and feel with terminal-style sounds.'
)
with open('TODO.md', 'w') as f:
    f.write(todo_content)

# Update VERSION file (Patch bump)
with open('VERSION', 'r') as f:
    current_version = f.read().strip()

parts = current_version.split('.')
parts[2] = str(int(parts[2]) + 1)
new_version = '.'.join(parts)

with open('VERSION', 'w') as f:
    f.write(new_version)

# Update HANDOFF.md
handoff_content = f"""# Agent Handoff Document

## Current State
- The AgentIRC system is fully operational.
- The `feature/agentirc-configuration-and-tools` phase was completed.
- The `sandbox file tool` feature was completed securely preventing traversal outside `.sandbox/`.
- I have just completed the `terminal sounds` feature, adding a `beep.wav` file to the UI that triggers on incoming chats and `/slap` actions using `cl.Audio`.
- The next developer should review `TODO.md` to select the next feature.
"""
with open('HANDOFF.md', 'w') as f:
    f.write(handoff_content)

print(f"Bumped version to {new_version}")
