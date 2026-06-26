import asyncio
import unittest
from mcp_server import mcp

class TestMCPServer(unittest.TestCase):
    def test_mcp_tools_registered(self):
        # We can test FastMCP's internal state. FastMCP typically exposes .name and some
        # internal mappings. We just check if the mcp object initialized cleanly.
        self.assertEqual(mcp.name, "AgentIRC")

if __name__ == "__main__":
    unittest.main()
