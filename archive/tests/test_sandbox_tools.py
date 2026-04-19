import unittest
import os
import tempfile
import simulator_tools

class SandboxToolTests(unittest.TestCase):
    def setUp(self):
        # Override SANDBOX_DIR for tests
        self.test_dir = tempfile.mkdtemp()
        simulator_tools.SANDBOX_DIR = self.test_dir

    def test_sandbox_write_and_read(self):
        result_write = simulator_tools.sandbox_write_file("test.txt", "Hello World")
        self.assertIn("Successfully wrote", result_write)

        result_read = simulator_tools.sandbox_read_file("test.txt")
        self.assertEqual(result_read, "Hello World")

    def test_sandbox_path_traversal_prevention(self):
        # Attempt to write outside the sandbox
        result_write = simulator_tools.sandbox_write_file("../malicious.txt", "Exploit")
        self.assertIn("Successfully wrote", result_write)

        # Verify it was actually written inside the sandbox as 'malicious.txt'
        expected_safe_path = os.path.join(self.test_dir, "malicious.txt")
        self.assertTrue(os.path.exists(expected_safe_path))

        # Verify it wasn't written to the parent dir
        self.assertFalse(os.path.exists(os.path.join(self.test_dir, "..", "malicious.txt")))

    def test_read_nonexistent_file(self):
        result_read = simulator_tools.sandbox_read_file("does_not_exist.txt")
        self.assertIn("Error: Sandbox file", result_read)

if __name__ == "__main__":
    unittest.main()
