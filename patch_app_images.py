import re
with open('app.py', 'r') as f:
    content = f.read()

replacement = """@cl.on_message
async def handle_message(message: cl.Message):
    content = message.content.strip()
    images = []
    if message.elements:
        for element in message.elements:
            if "image" in element.mime:
                images.append(element)

    if not content and not images:
        await send_system_notice("Empty messages are ignored.")
        return

    config = get_config()

    if images:
        content += "\\n[User attached images]"

    add_history_entry(author=config["nick"], content=content, kind="user")

    parsed_command = parse_command(content)"""

content = re.sub(
    r'@cl\.on_message\nasync def handle_message\(message: cl\.Message\):\n    content = message\.content\.strip\(\)\n    if not content:\n        await send_system_notice\("Empty messages are ignored\."\)\n        return\n\n    config = get_config\(\)\n    add_history_entry\(author=config\["nick"\], content=content, kind="user"\)\n\n    parsed_command = parse_command\(content\)',
    replacement,
    content
)

with open('app.py', 'w') as f:
    f.write(content)
