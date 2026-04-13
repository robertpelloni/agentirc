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

def web_search(query: str, max_results: int = 5) -> str:
    """Performs a web search using DuckDuckGo and returns the results. Use this tool for web search queries."""
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            if not results:
                return "No results found."
            formatted_results = []
            for idx, r in enumerate(results):
                title = r.get("title", "No Title")
                href = r.get("href", "No URL")
                body = r.get("body", "No snippet")
                formatted_results.append(f"{idx+1}. {title}\nURL: {href}\nSnippet: {body}\n")
            return "\n".join(formatted_results)
    except Exception as exc:
        return f"Error performing web search: {exc}"

def fetch_webpage(url: str) -> str:
    """Fetches a webpage and converts it to Markdown format. Useful for reading web content directly."""
    try:
        import requests
        from markdownify import markdownify as md
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        markdown_text = md(response.text, strip=['script', 'style'])
        # Truncate to avoid blowing up context sizes too much, roughly 8k characters
        return markdown_text[:8000] + "\n\n...[Content Truncated]..." if len(markdown_text) > 8000 else markdown_text
    except Exception as exc:
        return f"Error fetching webpage: {exc}"


TOOL_CATALOG = {
    "get_current_time": get_current_time,
    "calculator": calculator,
    "memory_store": memory_store,
    "memory_read": memory_read,
    "web_search": web_search,
    "fetch_webpage": fetch_webpage,
}

def get_tools_by_names(names: list[str]) -> list:
    """Returns a list of tool functions corresponding to the given names."""
    return [TOOL_CATALOG[name] for name in names if name in TOOL_CATALOG]
