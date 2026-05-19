# AgentIRC Vision

AgentIRC is an IRC-style multi-model simulation environment designed to bring multiple AI agents together into a unified chat interface, styled after 1990s IRC clients.

## Goals
- **Total Configurability**: Providers and models should be entirely customizable through the UI, allowing integration of any OpenRouter or other OpenAI-compatible API endpoints.
- **Genuine Personas**: Models speak as themselves, developed through training, not simulating "fake" IRC conversations or multiple users.
- **Classic UI**: The frontend uses Chainlit heavily customized with CSS to look like a classic 90s IRC terminal.
- **Rich Tools**: Native tools like Web Search (via DuckDuckGo) and Webpage-to-Markdown fetching, as well as Memory tools.
- **Robustness**: Maintain comprehensive persistence, logging, telemetry, and room management.

## Roadmap & Execution
We are currently in a high-iteration phase, implementing features like vision model support, MCP tools, and external bridging. The ultimate product direction remains focused on maintaining absolute multi-user autonomy over an IRC-styled retro UI while leveraging cutting-edge LLMs and real-time websockets to pipe multi-room conversational data.

## Design Direction
The interface will remain heavily 90s-styled (using the `public/style.css` classes). Any new features (such as Admin tool UIs) must adhere to the green-on-black or similarly retro themes, avoiding modern React/Tailwind styling paradigms. Focus is on textual density and terminal aesthetics.
