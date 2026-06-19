# Deployment Instructions

1. Ensure Python 3.14.3 is installed.
2. Clone repository.
3. Install requirements using `pip install -r requirements.txt`.
4. Configure models in `agents_config.json` and API endpoint in `config.toml`.
5. Run using `python run.py`.

## Environment Variables
- `OPENROUTER_API_KEY`: Required if using OpenRouter models.
- `CHAINLIT_AUTH_SECRET`: **Required** for the multi-user authentication system to boot. You must generate a random secure string (e.g., `openssl rand -base64 32`) and add it to your `.env` file. If missing, Chainlit will refuse to start.
- `AGENTIRC_USER_<USERNAME>`: Optional. Defines a password for `<USERNAME>`. For example, setting `AGENTIRC_USER_ADMIN=supersecret` allows the user `admin` to log in with `supersecret`.

## Versioning
The single source of truth for the project version is `VERSION.md`. The current deployed version is `0.43.0`.


### Version 0.32.0 Updates
Ensure `httpx` is installed and up-to-date for async tool I/O execution. Run `pip install -r requirements.txt`.
### Version 0.35.0 Updates
- Introduced a native MCP Server via `mcp.server.fastmcp`. Ensure the `mcp` package is installed (`pip install mcp`). To launch, run `python mcp_server.py`.
### Version 0.36.0 Updates
- Introduced native local LLM support via Ollama. Ensure Ollama is running locally on port 11434 if you append models prefixed with `ollama/`.
### Version 0.37.0 Updates
- Integrated a custom frontend audio engine in `public/irc.js`. No new backend dependencies required.
### Version 0.41.0 Updates
- Added `mcp` connector adapter. External systems can now consume outbound JSON-RPC payloads via `--connector mcp --endpoint <URL>`.
### Version 0.43.0 Updates
- Added `headless_irc.py` for fully headless operations driven by IRC clients. To run the headless bot, execute `python headless_irc.py --server <irc_server> --channel <channel> --nick <bot_nick>`. Ensure the bot's environment contains all required API variables.
