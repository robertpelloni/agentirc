import datetime

new_entry = f"""
## 0.20.0 - {datetime.date.today().isoformat()}
- Added configurable providers and models (`agents_config.json`, `config.toml`).
- Added web search and webpage fetching capabilities via `duckduckgo-search` and `markdownify`.
- Implemented `/slap` tool for the 1990s IRC interface.
- Enabled file and image upload processing, forwarding them as multimodal payloads to the agents.
- Updated system instructions to enforce authentic model personas and immediately emit topic on room activation.
- Extensively expanded project documentation (TODO.md, ROADMAP.md, VISION.md, MEMORY.md, DEPLOY.md, LLM instructions).

"""

with open("CHANGELOG.md", "r") as f:
    content = f.read()

content = content.replace("# Changelog\n", "# Changelog\n" + new_entry)

with open("CHANGELOG.md", "w") as f:
    f.write(content)
