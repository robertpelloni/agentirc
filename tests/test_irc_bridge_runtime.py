import unittest

from irc_bridge_runtime import (
    MAX_PRIVMSG_LEN,
    build_irc_message,
    chunk_irc_message,
    normalize_irc_text,
    payload_to_irc_lines,
)


ROOM_PAYLOAD = {
    "kind": "room_snapshot",
    "room": "lobby",
    "topic": "Testing",
    "entries": [
        {"author": "Claude", "content": "hello there"},
        {"author": "Gemini", "content": "general kenobi"},
    ],
}


class IrcBridgeRuntimeTests(unittest.TestCase):
    def test_normalize_irc_text(self):
        text = normalize_irc_text("hello\nworld\r\nagain")
        self.assertEqual(text, "hello world again")

    def test_chunk_irc_message(self):
        text = "x" * (MAX_PRIVMSG_LEN + 20)
        chunks = chunk_irc_message(text)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk) <= MAX_PRIVMSG_LEN for chunk in chunks))

    def test_build_irc_message(self):
        message = build_irc_message(ROOM_PAYLOAD)
        self.assertIn("room_snapshot", message)
        self.assertIn("lobby", message)
        self.assertIn("Claude", message)

    def test_payload_to_irc_lines(self):
        lines = payload_to_irc_lines(ROOM_PAYLOAD, "#agentirc")
        self.assertTrue(lines)
        self.assertTrue(all(line.startswith("PRIVMSG #agentirc :") for line in lines))
        self.assertTrue(all(line.endswith("\r\n") for line in lines))


if __name__ == "__main__":
    unittest.main()
