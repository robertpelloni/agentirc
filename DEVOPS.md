# DevOps & Deployment

## Environment Setup
- Python 3.14+ recommended.
- Install dependencies: `pip install -r requirements.txt`.
- Copy `.env.example` to `.env` and fill `OPENROUTER_API_KEY`.

## Running the App
- Run `chainlit run app.py -w` to start the web interface.

## Tests
- Run `python -m unittest discover tests` to ensure core logic operates correctly.

## State Management
- `simulator_state.json` persists lineups, personas, jobs, and agent configurations. Ensure this file is backed up.
