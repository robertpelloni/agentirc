import pytest
import json
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

# In order to test app.py, we need to mock a lot of Chainlit state.
# Since it's tightly coupled to Chainlit, we will test the logic of `listen_to_websocket` directly.
import app

@pytest.mark.asyncio
async def test_listen_to_websocket_valid_mcp():
    # Mock dependencies
    session_team = MagicMock()
    send_system_notice = AsyncMock()
    stream_agent = AsyncMock()

    # Valid MCP Payload
    valid_payload = {
        "jsonrpc": "2.0",
        "method": "test/method",
        "params": {"key": "value"},
        "id": 1
    }

    # Mock websockets.connect context manager
    mock_ws = AsyncMock()
    mock_ws.__aenter__.return_value = mock_ws
    mock_ws.__aiter__.return_value = [json.dumps(valid_payload)]

    with patch("app.websockets.connect", return_value=mock_ws):
        await app.listen_to_websocket("ws://fake.uri", session_team, send_system_notice, stream_agent)

    # Verify notices and streams
    assert send_system_notice.call_count == 2
    # call 1: connected
    # call 2: [BRIDGED] Received MCP 'test/method' payload: {'key': 'value'}

    assert stream_agent.call_count == 1
    # Check that stream_agent was called with the payload params
    args, kwargs = stream_agent.call_args
    assert args[0] == session_team
    assert json.loads(args[1]) == {"key": "value"}
    assert kwargs.get("telemetry_name") == "websocket"

@pytest.mark.asyncio
async def test_listen_to_websocket_invalid_mcp():
    session_team = MagicMock()
    send_system_notice = AsyncMock()
    stream_agent = AsyncMock()

    # Invalid MCP Payload (missing jsonrpc 2.0)
    invalid_payload = {
        "method": "test/method",
        "params": {"key": "value"}
    }

    mock_ws = AsyncMock()
    mock_ws.__aenter__.return_value = mock_ws
    mock_ws.__aiter__.return_value = [json.dumps(invalid_payload)]

    with patch("app.websockets.connect", return_value=mock_ws):
        await app.listen_to_websocket("ws://fake.uri", session_team, send_system_notice, stream_agent)

    assert stream_agent.call_count == 0
    # call 1: connected
    # call 2: Received invalid payload: strictly requires MCP JSON-RPC 2.0 compliance.
    assert "invalid payload" in send_system_notice.call_args_list[1][0][0]
