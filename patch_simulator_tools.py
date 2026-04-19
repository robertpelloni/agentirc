import re
with open('simulator_tools.py', 'r') as f:
    content = f.read()

tools_code = """
import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from duckduckgo_search import DDGS

def web_search(query: str, max_results: int = 5) -> str:
    \"\"\"Searches the web using DuckDuckGo and returns summaries of the top results.\"\"\"
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
    \"\"\"Fetches a webpage and converts its content to Markdown.\"\"\"
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        return md(str(soup), heading_style="ATX").strip()[:10000] # Limit length
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
"""

content = re.sub(
    r'TOOL_CATALOG = \{.*?\}',
    tools_code.strip(),
    content,
    flags=re.DOTALL
)

with open('simulator_tools.py', 'w') as f:
    f.write(content)
