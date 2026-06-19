import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from app import handle_command

class TestAddModelCommand(unittest.IsolatedAsyncioTestCase):

    @patch('app.get_persistent_state')
    @patch('app.get_config')
    @patch('app.send_system_notice')
    async def test_add_model_insufficient_args(self, mock_send_system_notice, mock_get_config, mock_get_persistent_state):
        mock_get_config.return_value = {"enabled_agents": []}
        mock_get_persistent_state.return_value = {}
        args = "TestBot"
        result = await handle_command("/add-model", args)
        self.assertTrue(result)
        mock_send_system_notice.assert_called_with(
            'Usage: `/add-model <name> <provider> <model_id> ["persona override"]`'
        )

    @patch('app.rebuild_team')
    @patch('app.get_persistent_state')
    @patch('app.get_config')
    @patch('app.get_agent_specs')
    @patch('app.persist_state')
    @patch('app.send_system_notice')
    @patch('app.update_agent_specs')
    async def test_add_model_success(
        self,
        mock_update_agent_specs,
        mock_send_system_notice,
        mock_persist_state,
        mock_get_agent_specs,
        mock_get_config,
        mock_get_persistent_state,
        mock_rebuild_team
    ):
        config = {"enabled_agents": [], "room_name": "TestRoom", "mode": "discuss", "scenario": "Test", "topic": "Testing"}
        agent_specs = {}

        mock_get_config.return_value = config
        mock_get_agent_specs.return_value = agent_specs
        mock_get_persistent_state.return_value = {}

        args = 'TestBot openai gpt-4o "A test bot"'

        result = await handle_command("/add-model", args)

        self.assertTrue(result)
        mock_update_agent_specs.assert_called_once()
        updated_dict = mock_update_agent_specs.call_args[0][0]
        self.assertIn("TestBot", updated_dict)
        self.assertEqual(updated_dict["TestBot"]["model"], "openai/gpt-4o")
        self.assertEqual(updated_dict["TestBot"]["bio"], "A test bot")
        self.assertIn("TestBot", config["enabled_agents"])
        mock_rebuild_team.assert_called_once()
        mock_send_system_notice.assert_called_with("Model **TestBot** added to catalog and enabled. Restart session if needed to fully map catalog changes.")

if __name__ == '__main__':
    unittest.main()
