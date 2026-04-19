import unittest
import tempfile
import json
from pathlib import Path
from simulator_core import resolve_replay_file

class TestReplayNameResolution(unittest.TestCase):
    def test_named_replay_resolution(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            dir_path = Path(temp_dir)
            file1 = dir_path / "agentirc-123.json"
            file2 = dir_path / "agentirc-456.json"

            # Create mock files
            file1.write_text(json.dumps({"history": []}))
            file2.write_text(json.dumps({"history": []}))

            # Resolve exact name
            result = resolve_replay_file("agentirc-456.json", export_dir=dir_path)
            self.assertEqual(result.name, "agentirc-456.json")

if __name__ == "__main__":
    unittest.main()
