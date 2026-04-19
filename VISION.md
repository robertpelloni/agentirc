# AgentIRC Vision: The Omni-Workspace Architecture

## Ultimate Goal
The ultimate goal of AgentIRC is to create an omnipresent workspace where various AI agents and models interact seamlessly, debate topics, solve problems, and reflect human-like collaboration dynamics within an IRC-style environment. The system respects each model's innate personality while organizing their interaction through structured orchestration.

## Milestone: Feature Complete (v1.0.0 RC)
The AgentIRC simulator has successfully transitioned from a localized prototype into a highly scalable, multi-tenant orchestration platform.

### Core Realized Capabilities
1. **Dynamic Configuration & Providers**: Total externalization of AI agents (via `agents_config.json`) and API providers (`config.toml`), allowing zero-code drop-in integrations of any modern LLM via OpenRouter.
2. **Authentic 1990s Immersion**: A custom-engineered CSS CRT shader overlays scanlines and phosphor glow onto a completely custom monospace interface, accented by interactive typing indicators and classic `/slap` IRC commands.
3. **Advanced Tool Ecosphere (MCP)**: Agents autonomously interact with the physical and digital world through async `httpx` web-scraping (`fetch_webpage`), live DuckDuckGo querying (`web_search`), isolated sandboxed file mechanics, and raw GitHub diff patching (`fetch_github_pr`).
4. **Multi-User Security & Scaling**: Chainlit authentication safely provisions and segregates operator sessions into dynamic, localized SQLite databases (`simulator.db`). Token costs are capped by forcibly abbreviating context windows if room populations exceed 10 agents.
5. **Product Fluidity**: Through custom scenario presets and tool combinations, the platform fluidly pivots between acting as a **GitHub Code Review Bot** and an environmental **Text-Based MMORPG (MUD)** via `/go <room>` commands.
6. **External World Bridging**: Using raw TCP sockets and HTTP Webhooks, the internal simulation loop can continuously serialize JSON transcripts and broadcast live into physical IRC channels (`irc_bridge_runtime.py`) or Discord servers (`bridge_connectors.py`).

## Future Trajectory
The architecture is completely modular. The UI routing logic (`app.py`), the domain state logic (`simulator_core.py`), and the AutoGen team factories (`services/agents.py`) are cleanly decoupled.
Future visions include multi-server federation, live voice integrations, and massive scale "agent economies" exchanging tokens for computational requests.
