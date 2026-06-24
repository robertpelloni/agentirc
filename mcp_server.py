import asyncio
import logging
from mcp.server.fastmcp import FastMCP
from simulator_tools import TOOL_CATALOG

logger = logging.getLogger("mcp_server")
logging.basicConfig(level=logging.INFO)

mcp = FastMCP("AgentIRC")

def _register_tools():
    """Register all tools from the catalog to the MCP server."""
    count = 0
    for tool_name, tool_func in TOOL_CATALOG.items():
        try:
            mcp.tool(name=tool_name)(tool_func)
            count += 1
            logger.debug(f"Registered MCP tool: {tool_name}")
        except Exception as e:
            logger.error(f"Failed to register tool {tool_name}: {e}")
    logger.info(f"Registered {count} total tools into MCP.")

_register_tools()

if __name__ == "__main__":
    logger.info("Starting AgentIRC MCP Server...")
    mcp.run()
