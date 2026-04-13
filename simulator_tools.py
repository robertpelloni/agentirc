import requests
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

def web_search(query: str, max_results: int = 5) -> str:
    try:
        results = DDGS().text(query, max_results=max_results)
        if not results:
            return "No results found."
        formatted = []
        for i, res in enumerate(results):
            formatted.append(f"{i+1}. {res.get('title', 'No Title')} - {res.get('href', 'No URL')}\\n{res.get('body', 'No snippet')}")
        return "\\n\\n".join(formatted)
    except Exception as e:
        return f"Web search error: {e}"

def fetch_webpage(url: str) -> str:
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        for script in soup(["script", "style"]):
            script.decompose()
        return md(str(soup), heading_style="ATX").strip()[:10000]
    except Exception as e:
        return f"Error fetching webpage: {e}"
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
    return [TOOL_CATALOG[name] for name in names if name in TOOL_CATALOG]
