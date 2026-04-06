import os
import unittest

LIVE_ENABLED = os.getenv("RUN_LIVE_INTEGRATION") == "1"
HAS_KEY = bool(os.getenv("OPENROUTER_API_KEY"))


@unittest.skipUnless(LIVE_ENABLED and HAS_KEY, "Set RUN_LIVE_INTEGRATION=1 and OPENROUTER_API_KEY to run live integration tests.")
class LiveIntegrationTests(unittest.TestCase):
    def test_live_environment_is_configured(self):
        self.assertTrue(LIVE_ENABLED)
        self.assertTrue(HAS_KEY)

    def test_live_placeholder(self):
        # Placeholder smoke test to make opt-in live execution explicit.
        # Future work should exercise OpenRouter-backed streaming/judging/bridge flows.
        self.assertEqual(os.getenv("RUN_LIVE_INTEGRATION"), "1")


if __name__ == "__main__":
    unittest.main()
