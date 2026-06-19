import asyncio
from mcp.server.fastmcp import FastMCP
from simulator_tools import TOOL_CATALOG

mcp = FastMCP("AgentIRC")

# Register all tools from the catalog
for tool_name, tool_func in TOOL_CATALOG.items():
    # Note: FastMCP uses the function's name and docstring automatically,
    # but we can explicitly name it if needed. The decorator approach works.
    mcp.tool(name=tool_name)(tool_func)

if __name__ == "__main__":
    mcp.run()
