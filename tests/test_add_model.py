import unittest
import asyncio
from unittest.mock import patch, MagicMock

# Allow chainlit to load normally
import chainlit as cl

# Patch out chainlit user session
original_get = cl.user_session.get
cl.user_session.get = MagicMock(return_value={"enabled_agents": [], "nick": "TestUser"})

from app import handle_command, get_agent_specs, get_config

class TestAddModelCommand(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        pass

    @patch('app.rebuild_team')
    @patch('app.get_persistent_state')
    @patch('app.get_config')
    @patch('app.get_agent_specs')
    @patch('app.save_agents_config')
    @patch('app.send_system_notice')
    async def test_add_model_success(self, mock_send_system_notice, mock_save_agents_config, mock_get_agent_specs, mock_get_config, mock_get_persistent_state, mock_rebuild_team):
        config = {"enabled_agents": [], "room_name": "TestRoom", "mode": "discuss", "scenario": "Test", "topic": "Testing"}
        agent_specs = {}

        mock_get_config.return_value = config
        mock_get_agent_specs.return_value = agent_specs
        mock_get_persistent_state.return_value = {}

        args = 'TestBot openai gpt-4o "A test bot"'

        import app
        original_agent_specs = app.AGENT_SPECS
        app.AGENT_SPECS = agent_specs

        result = await handle_command("/add-model", args)

        self.assertTrue(result)
        self.assertIn("TestBot", app.AGENT_SPECS)
        self.assertEqual(app.AGENT_SPECS["TestBot"]["model"], "openai/gpt-4o")
        self.assertEqual(app.AGENT_SPECS["TestBot"]["bio"], "A test bot")
        self.assertIn("TestBot", config["enabled_agents"])
        mock_save_agents_config.assert_called_once()
        mock_send_system_notice.assert_called_with('Model **TestBot** added to catalog and enabled. Restart session if needed to fully map catalog changes.')
        mock_rebuild_team.assert_called_once()

        app.AGENT_SPECS = original_agent_specs

    @patch('app.get_persistent_state')
    @patch('app.get_config')
    @patch('app.get_agent_specs')
    @patch('app.send_system_notice')
    async def test_add_model_insufficient_args(self, mock_send_system_notice, mock_get_agent_specs, mock_get_config, mock_get_persistent_state):
        args = 'TestBot openai'

        config = {"enabled_agents": []}
        mock_get_config.return_value = config
        mock_get_persistent_state.return_value = {}

        result = await handle_command("/add-model", args)

        self.assertTrue(result)
        mock_send_system_notice.assert_called_once_with('Usage: `/add-model <name> <provider> <model_id> ["persona override"]`')

if __name__ == '__main__':
    unittest.main()
