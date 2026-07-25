# Headless IRC Client Integration Guide

## Overview
AgentIRC is designed to support a fully headless mode driven entirely by IRC clients (`headless_irc.py`). This allows standard IRC clients (e.g., mIRC, Irssi, HexChat) or automated IRC bots to connect to a standard IRC server and bridge real-time messages directly into the AutoGen swarm, bypassing the Chainlit UI.

## Architecture
- **`headless_irc.py`**: Acts as an asyncio-based IRC bot. It connects natively to an IRC server, listens for `PING` / `MODE` / `001` messages to manage connection lifecycle, and intercepts `PRIVMSG` events.
- **Swarm Bridging**: When `PRIVMSG` events are captured, they bypass Chainlit and are routed directly into the AutoGen swarm orchestration loop.

## Setup Instructions
1. Ensure the `headless_irc.py` script is executable and the dependencies are installed.
2. Define the target IRC server, port, nickname, and channel in the configuration or environment variables.
3. Run the client via `python headless_irc.py`.
