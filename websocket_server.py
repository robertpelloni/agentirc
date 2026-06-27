import asyncio
import json
import logging
import websockets
import os
from datetime import datetime

logger = logging.getLogger("websocket_server")
logging.basicConfig(level=logging.INFO)

# A registry of active connections by room
# dict[room_name, set[websockets.WebSocketServerProtocol]]
connected_clients: dict[str, set] = {}

async def register(websocket, room: str):
    if room not in connected_clients:
        connected_clients[room] = set()
    connected_clients[room].add(websocket)
    logger.info(f"Client connected to room {room}. Total: {len(connected_clients[room])}")

async def unregister(websocket, room: str):
    if room in connected_clients:
        connected_clients[room].remove(websocket)
        logger.info(f"Client disconnected from room {room}. Remaining: {len(connected_clients[room])}")
        if not connected_clients[room]:
            del connected_clients[room]

async def broadcast_to_room(room: str, message: str, sender=None):
    if room in connected_clients:
        tasks = []
        for client in connected_clients[room]:
            if client != sender:
                tasks.append(asyncio.create_task(client.send(message)))
        if tasks:
            await asyncio.wait(tasks)
            logger.debug(f"Broadcasted to {len(tasks)} clients in room {room}.")

async def ws_handler(websocket, path):
    # Determine room from path e.g., /ws/room_alpha -> room_alpha
    room = path.strip("/").split("/")[-1]
    if not room:
        room = "default"

    await register(websocket, room)
    try:
        async for message in websocket:
            try:
                # We expect inbound messages to be JSON
                data = json.loads(message)

                # Check for MCP JSON-RPC 2.0 format
                if data.get("jsonrpc") == "2.0":
                    logger.info(f"Received MCP payload in room {room}: {data.get('method')}")

                    # Ensure retro UI feedback wrapper
                    payload = data.get("params", {}).get("payload", {})
                    # This would typically route into the simulator_core inbox/message system

                    # Broadcast the received message to everyone else in the room
                    await broadcast_to_room(room, message, sender=websocket)
                else:
                    logger.warning(f"Received non-MCP compliant message in room {room}.")
            except json.JSONDecodeError:
                logger.error(f"Received invalid JSON in room {room}.")
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        await unregister(websocket, room)

async def main():
    port = int(os.environ.get("WEBSOCKET_PORT", 8765))
    logger.info(f"Starting AgentIRC WebSocket Server on port {port}...")
    async with websockets.serve(lambda ws: ws_handler(ws, ws.request.path), "localhost", port):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
