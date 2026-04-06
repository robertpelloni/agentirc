from datetime import datetime

# Global memory for tools
_SHARED_MEMORY: dict[str, str] = {}


def get_current_time() -> str:
    """Returns the current date and time in ISO format."""
    return datetime.now().isoformat()


def calculator(expression: str) -> str:
    """Evaluates a basic math expression (e.g. "5 + 2 * 3"). Only supports +, -, *, /, and numbers."""
    try:
        # A very restricted eval for basic math to prevent arbitrary code execution
        allowed_chars = "0123456789+-*/(). "
        if any(c not in allowed_chars for c in expression):
            return "Error: Invalid characters in expression. Only basic math is allowed."
        # Not fully secure against all Python eval vectors if functions exist, but sufficient for this demo.
        # Given it's restricted by allowed_chars, it's fairly safe.
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as exc:
        return f"Error evaluating expression: {exc}"


def memory_store(key: str, value: str) -> str:
    """Stores a value in the shared memory under the given key."""
    _SHARED_MEMORY[key] = value
    return f"Successfully stored key '{key}'."


def memory_read(key: str) -> str:
    """Retrieves a value from the shared memory by key. Returns 'not found' if it does not exist."""
    return _SHARED_MEMORY.get(key, f"Error: Key '{key}' not found.")


TOOL_CATALOG = {
    "get_current_time": get_current_time,
    "calculator": calculator,
    "memory_store": memory_store,
    "memory_read": memory_read,
}

def get_tools_by_names(names: list[str]) -> list:
    """Returns a list of tool functions corresponding to the given names."""
    return [TOOL_CATALOG[name] for name in names if name in TOOL_CATALOG]
