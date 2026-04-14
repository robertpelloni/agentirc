import re

with open('simulator_core.py', 'r') as f:
    content = f.read()

# Add DEFAULT_AGENT_SPECS at the top or near make_default_store
default_specs = """
DEFAULT_AGENT_SPECS = {
    "Claude": {
        "model": "anthropic/claude-sonnet-4.6",
        "color": "#ffaa00",
        "bio": "Nuanced and detailed.",
        "pricing": {"input_per_million": 3.0, "output_per_million": 15.0},
    },
    "GPT_5": {
        "model": "openai/gpt-5.3-chat",
        "color": "#00ff00",
        "bio": "Logical and concise.",
        "pricing": {"input_per_million": 1.25, "output_per_million": 10.0},
    },
    "Gemini": {
        "model": "google/gemini-3.1-flash-image-preview",
        "color": "#44aaff",
        "bio": "Creative and fact-driven.",
        "pricing": {"input_per_million": 0.35, "output_per_million": 1.05},
    },
    "Grok": {
        "model": "x-ai/grok-4.1-fast",
        "color": "#ffffff",
        "bio": "Rebellious and witty.",
        "pricing": {"input_per_million": 5.0, "output_per_million": 15.0},
    },
    "Qwen": {
        "model": "qwen/qwen3.6-plus-preview:free",
        "color": "#ff55ff",
        "bio": "Versatile power.",
        "pricing": {"input_per_million": 0.0, "output_per_million": 0.0},
    },
    "Kimi": {
        "model": "moonshotai/kimi-k2.5",
        "color": "#ffff00",
        "bio": "Deep reasoning.",
        "pricing": {"input_per_million": 0.6, "output_per_million": 2.5},
    },
}

def make_default_store() -> dict[str, Any]:
    return {
        "saved_lineups": {},
        "saved_personas": {},
        "saved_jobs": {},
        "saved_bridge_policies": {},
        "agent_specs": DEFAULT_AGENT_SPECS,
    }
"""

content = re.sub(
    r'def make_default_store\(\) -> dict\[str, Any\]:.*?(?=\n\n\n)',
    default_specs.strip(),
    content,
    flags=re.DOTALL
)

with open('simulator_core.py', 'w') as f:
    f.write(content)
