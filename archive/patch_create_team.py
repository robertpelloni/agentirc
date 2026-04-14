import re
with open('app.py', 'r') as f:
    content = f.read()

system_message_code = """        system_message = (
            f"You are {display_agent_name(name)}. You are speaking as yourself with your own personality developed through training. "
            "Do NOT simulate a fake IRC conversation or simulate multiple users. You are in an IRC chat room but you are just one participant. "
            f"Room: {config['room_name']}. Mode: {config['mode'].upper()}. Scenario: {config['scenario']}. "
            f"Topic: {config['topic']}. Persona: {persona} "
            f"Peers: {', '.join(peers) if peers else 'none'}. "
            f"Moderator mode: {config['moderator_mode']} ({MODERATOR_MODES[config['moderator_mode']]}) "
            "Respond in plain text with a concise, useful IRC-style reply. "
            "Stay in character, avoid markdown headers, and keep it easy to scan."
        )"""

content = re.sub(
    r'        system_message = \(\n            f"You are \{display_agent_name\(name\)\} in an IRC-style multi-model simulation\. "\n            f"Room: \{config\[\'room_name\'\]\}\. Mode: \{config\[\'mode\'\]\.upper\(\)\}\. Scenario: \{config\[\'scenario\'\]\}\. "\n            f"Topic: \{config\[\'topic\'\]\}\. Persona: \{persona\} "\n            f"Peers: \{.*?\. "\n            f"Moderator mode: \{config\[\'moderator_mode\'\]\} \(\{MODERATOR_MODES\[config\[\'moderator_mode\'\]\]\}\) "\n            "Respond in plain text with a concise, useful IRC-style reply\. "\n            "Stay in character, avoid markdown headers, and keep it easy to scan\."\n        \)',
    system_message_code,
    content,
    flags=re.DOTALL
)

with open('app.py', 'w') as f:
    f.write(content)
