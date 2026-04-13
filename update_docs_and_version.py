import re
import os

# Update TODO.md checkbox
with open('TODO.md', 'r') as f:
    todo_content = f.read()
todo_content = todo_content.replace(
    '- [ ] Expand tool capabilities, potentially adding read/write file access within a safe sandbox.',
    '- [x] Expand tool capabilities, potentially adding read/write file access within a safe sandbox.'
)
with open('TODO.md', 'w') as f:
    f.write(todo_content)

# Update VERSION file
with open('VERSION', 'r') as f:
    current_version = f.read().strip()

parts = current_version.split('.')
parts[1] = str(int(parts[1]) + 1)
new_version = '.'.join(parts)

with open('VERSION', 'w') as f:
    f.write(new_version)

# Update HANDOFF.md
handoff_content = f"""# Agent Handoff Document

## Current State
- The AgentIRC system is fully operational.
- The `feature/agentirc-configuration-and-tools` phase was completed.
- I have just completed the `sandbox file tool` feature, which adds `sandbox_read_file` and `sandbox_write_file` safe interactions. The `.sandbox/` directory isolates these operations.
- The next developer should review `TODO.md` to select the next feature, perhaps focusing on robust user authentication or adding terminal sound effects to the frontend UI.
"""
with open('HANDOFF.md', 'w') as f:
    f.write(handoff_content)

print(f"Bumped version to {new_version}")
