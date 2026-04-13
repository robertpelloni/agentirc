import re
with open('app.py', 'r') as f:
    content = f.read()

replacement = """@cl.on_message
async def handle_message(message: cl.Message):
    content = message.content.strip()
    images = []

    # Process images for vision-capable models (using AutoGen MultiModalMessage)
    # We will pass multi-modal content to AutoGen
    from autogen_core import Image
    from PIL import Image as PILImage
    import io

    # Check elements for images
    image_elements = []
    if message.elements:
        for element in message.elements:
            if "image" in element.mime:
                images.append(element)

    if not content and not images:
        await send_system_notice("Empty messages are ignored.")
        return

    config = get_config()

    history_content = content
    if images:
        history_content += "\\n[User attached images]"

    add_history_entry(author=config["nick"], content=history_content, kind="user")

    parsed_command = parse_command(content)
    if parsed_command:
        command, args = parsed_command
        try:
            await handle_command(command, args)
        except Exception as exc:
            record_error(config)
            await send_system_notice(f"Command failed: {exc}")
        return

    active_agents = list(config["enabled_agents"])
    if not active_agents:
        await send_system_notice("No agents enabled. Use `/enable <agent>`.")
        return

    try:
        from autogen_core import Image

        # Build prompt
        prompt_content = []
        if content:
            prompt_content.append(content)

        for img_elem in images:
            if hasattr(img_elem, 'path') and img_elem.path:
                try:
                    pil_img = PILImage.open(img_elem.path)
                    # Convert to RGB if needed
                    if pil_img.mode != 'RGB':
                        pil_img = pil_img.convert('RGB')
                    prompt_content.append(Image(pil_img))
                except Exception as e:
                    print(f"Failed to process image: {e}")

        prompt = prompt_content if len(prompt_content) > 1 else prompt_content[0] if prompt_content else content

        if content.startswith("@"):
            parts = content.split(" ", 1)
            raw_target = parts[0][1:]
            msg_body = parts[1] if len(parts) > 1 else ""
            target_name = resolve_agent_name(raw_target, list(get_agent_specs().keys()))
            if not target_name:
                await send_system_notice(f"Unknown agent: `{raw_target}`")
                return
            if target_name not in active_agents:
                await send_system_notice(f"{display_agent_name(target_name)} is disabled.")
                return

            # Note: We must recreate the target agent outside the GroupChat context to avoid loop errors
            target_agent = create_judge_agent(config) # Hack: create single agent
            # Actually, to run single agent, we need to extract from team or create new.
            from autogen_agentchat.agents import AssistantAgent
            spec = get_agent_specs()[target_name]
            target_agent = AssistantAgent(
                name=target_name,
                model_client=get_client(spec["model"]),
                system_message=f"You are {display_agent_name(target_name)}. Reply to this direct message.",
                tools=get_tools_by_names(config.get("enabled_tools", [])) or None,
            )

            prompt_dm = []
            if msg_body: prompt_dm.append(msg_body)
            for img in prompt_content:
                if isinstance(img, Image): prompt_dm.append(img)

            if not prompt_dm:
                prompt_dm = "Hello"

            dm_task = prompt_dm if len(prompt_dm) > 1 else prompt_dm[0] if prompt_dm else msg_body

            await send_system_notice(f"Private message to {display_agent_name(target_name)}...")
            await stream_agent(target_agent, dm_task, target_name=display_agent_name(target_name))
            return

        team = cl.user_session.get(SESSION_TEAM_KEY)
        await stream_agent(team, prompt)
    except Exception as exc:
        record_error(config)
        import traceback
        traceback.print_exc()
        await send_system_notice(f"Simulation failed: {exc}")"""

content = re.sub(
    r'@cl\.on_message\nasync def handle_message\(message: cl\.Message\):.*?(?=\n\n@cl\.on_chat_start)',
    replacement,
    content,
    flags=re.DOTALL
)

with open('app.py', 'w') as f:
    f.write(content)
