import re
with open('app.py', 'r') as f:
    content = f.read()

# make sure /topic and others sync functions don't have await
content = content.replace("def rebuild_team():\n    config = get_config()\n    team = create_team(config)\n    cl.user_session.set(SESSION_TEAM_KEY, team)\n    return team", "def rebuild_team():\n    config = get_config()\n    team = create_team(config)\n    cl.user_session.set(SESSION_TEAM_KEY, team)\n    return team")

with open('app.py', 'w') as f:
    f.write(content)
