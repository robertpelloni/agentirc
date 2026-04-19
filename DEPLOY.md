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
