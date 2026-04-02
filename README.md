# AgentIRC: The Multi-Model Broadcast Network

A high-performance, autonomous "IRC-style" multi-agent chat room. This client leverages **Microsoft AutoGen 0.4** and **Chainlit** to create a unified interface where the world's most advanced LLMs can be prompted simultaneously in a real-time broadcast format.

## 🚀 Advanced Features
- **Broadcast Mode**: Every user message triggers a sequential response from the entire model lineup.
- **Direct Messaging (DMs)**: Use `@AgentName <message>` to bypass the broadcast and speak to a single model.
- **IRC Commands**: Built-in support for `/help`, `/lineup`, and `/clear`.
- **Persistent Logging**: Every session is archived to `irc_session.log` for integration into the "Omni-Workspace" research pipeline.
- **Classic IRC Aesthetic**: Monospace "hacker" theme with `[TIMESTAMP] <NICK> MESSAGE` formatting.

## 🧠 Technical Findings & Analysis
### Python 3.14 "Hardening"
Operating on the experimental **Python 3.14.3** runtime presented significant challenges due to breaking changes in `asyncio`.
- **Finding**: Python 3.14 enforces strict task-context checks for `asyncio.wait_for` and `anyio`. Third-party libraries like `engineio` (used by Chainlit) fail these checks because they run service loops outside of formal tasks.
- **Solution**: Implemented a **Task Identity Lie** patch in `run.py`. This forces `anyio` and `asyncio` to synchronize their internal `_host_task` references with a persistent singleton `DummyTask`, bypassing weakref crashes and assertion errors.

### AutoGen 0.4 Migration
The project uses the new modular AutoGen architecture.
- **Event-Driven UI**: Unlike legacy AutoGen, 0.4 provides a `run_stream` API. We use this to capture `AgentEvent` and `ChatMessage` objects in real-time, allowing for a truly asynchronous chat experience.
- **Identifier Compliance**: Modular AutoGen requires agent names to be valid Python identifiers. We sanitized the lineup (e.g., `GPT-5` -> `GPT_5`) to ensure internal routing bus stability.

## 🛠 Tech Stack
- **Multi-Agent Orchestration**: AutoGen 0.4 (Modular)
- **Web UI**: Chainlit
- **API Gateway**: OpenRouter
- **Runtime**: Python 3.14.3

## 📋 Current Lineup
- **Claude 4.6**: Nuanced perspectives.
- **GPT-5.4**: Advanced logic.
- **Gemini 3.1**: Fact-driven creativity.
- **Grok 4.1**: Rebellious wit.
- **Qwen 3.6**: Versatile power.
- **Kimi 2.5**: Optimized insights.

## ⚡ Setup & Run
1. **Configure API**: Ensure your OpenRouter key is in `.env`.
2. **Install**: `pip install -r requirements.txt`
3. **Launch**: `python run.py`
