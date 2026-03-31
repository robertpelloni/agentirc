# AgentIRC

A multi-agent "IRC-style" chat room powered by **Microsoft AutoGen** and **Chainlit**. This client brings Claude, Gemini, Grok, and GPT-4o into a single room to debate, collaborate, and interact with you in real-time.

## Features
- **Multi-Model Integration:** Seamlessly connect to the world's top LLMs via OpenRouter.
- **IRC Dynamics:** Autonomous group chat where models read and respond to each other's context.
- **Rich UI:** Powered by Chainlit, featuring real-time message attribution and multi-agent visualization.
- **Human-in-the-Loop:** Toggleable interactive mode where the user can intervene in the AI discussion.
- **Session Persistence:** Context is maintained across messages for a true chat room experience.

## Tech Stack
- **Language:** Python 3.10+
- **Agent Framework:** AutoGen (0.2.x)
- **UI Framework:** Chainlit
- **API Gateway:** OpenRouter (OpenAI-compatible)

## Setup
1. **Clone & Submodule:** This is intended to run as a submodule in a monorepo or as a standalone tool.
2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Environment Variables:**
   Create a `.env` file with your OpenRouter key:
   ```env
   OPENROUTER_API_KEY=your_key_here
   ```
4. **Run:**
   ```bash
   chainlit run app.py -w
   ```

## Personas
- **Claude:** Nuanced and detailed perspectives.
- **GPT:** Logical and concise.
- **Gemini:** Creative and fact-driven.
- **Grok:** Rebellious and witty.
