import httpx
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from duckduckgo_search import DDGS
from datetime import datetime

_SHARED_MEMORY = {}

def get_current_time() -> str:
    return datetime.now().isoformat()

def calculator(expression: str) -> str:
    try:
        allowed_chars = "0123456789+-*/(). "
        if any(c not in allowed_chars for c in expression):
            return "Error: Invalid characters in expression."
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as exc:
        return f"Error evaluating expression: {exc}"

def memory_store(key: str, value: str) -> str:
    _SHARED_MEMORY[key] = value
    return f"Successfully stored key '{key}'."

def memory_read(key: str) -> str:
    return _SHARED_MEMORY.get(key, f"Error: Key '{key}' not found.")

import anyio.to_thread

async def web_search(query: str, max_results: int = 5) -> str:
    """Performs a web search using DuckDuckGo and returns the results. Use this tool for web search queries."""
    def sync_search():
        return list(DDGS().text(query, max_results=max_results))

    try:
        results = await anyio.to_thread.run_sync(sync_search)
        if not results:
            return "No results found."
        formatted = []
        for i, res in enumerate(results):
            formatted.append(f"{i+1}. {res.get('title', 'No Title')} - {res.get('href', 'No URL')}\n{res.get('body', 'No snippet')}")
        return "\n\n".join(formatted)
    except Exception as e:
        return f"Web search error: {e}"

async def fetch_webpage(url: str) -> str:
    """Fetches a webpage and converts it to Markdown format. Useful for reading web content directly."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=10.0)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            for script in soup(["script", "style"]):
                script.decompose()
            markdown_text = md(str(soup), heading_style="ATX").strip()
            return markdown_text[:8000] + "\n\n...[Content Truncated]..." if len(markdown_text) > 8000 else markdown_text
    except Exception as e:
        return f"Error fetching webpage: {e}"

TOOL_CATALOG = {
    "get_current_time": get_current_time,
    "calculator": calculator,
    "memory_store": memory_store,
    "memory_read": memory_read,
    "web_search": web_search,
    "fetch_webpage": fetch_webpage,
}

def get_tools_by_names(names: list[str]) -> list:
    return [TOOL_CATALOG[name] for name in names if name in TOOL_CATALOG]
