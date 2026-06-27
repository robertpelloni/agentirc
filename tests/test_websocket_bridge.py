import asyncio
import json
import unittest
import multiprocessing
import time
import websockets

import websocket_server

def start_server():
    asyncio.run(websocket_server.main())

class TestWebsocketServerBridge(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Start the WS server in a background process
        self.server_process = multiprocessing.Process(target=start_server)
        self.server_process.start()
        # Give it a moment to boot up
        time.sleep(1)

    async def asyncTearDown(self):
        self.server_process.terminate()
        self.server_process.join()

    async def test_mcp_realtime_bridge_exchange(self):
        uri = "ws://localhost:8765/test_room"

        async with websockets.connect(uri) as ws1, websockets.connect(uri) as ws2:
            # Send an MCP compliant message from ws1
            test_payload = {
                "jsonrpc": "2.0",
                "method": "agentirc/payload",
                "params": {
                    "transport": "websocket",
                    "payload": {"kind": "test", "data": "hello from ws1"}
                }
            }

            await ws1.send(json.dumps(test_payload))

            # ws2 should receive it (broadcast)
            response = await asyncio.wait_for(ws2.recv(), timeout=2.0)
            received_data = json.loads(response)

            self.assertEqual(received_data["jsonrpc"], "2.0")
            self.assertEqual(received_data["params"]["payload"]["data"], "hello from ws1")

if __name__ == "__main__":
    unittest.main()
