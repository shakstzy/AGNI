#!/usr/bin/env python3
import importlib.util
import unittest
from pathlib import Path

SKILL_PY = Path(__file__).resolve().parents[1] / "bluebubbles.py"
spec = importlib.util.spec_from_file_location("bluebubbles_mod", SKILL_PY)
bluebubbles = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bluebubbles)


class TestBlueBubbles(unittest.TestCase):
    def test_redact(self):
        secret = "super_secret_password"
        text = f"Failed to connect with super_secret_password to host"
        redacted = bluebubbles.redact(text, secret)
        self.assertNotIn("super_secret_password", redacted)
        self.assertIn("[redacted]", redacted)

    def test_sanitize_response_json(self):
        secret = "secret123"
        raw_json = b'{"status": 200, "token": "secret123", "message": "hello"}'
        sanitized = bluebubbles.sanitize_response(raw_json, secret)
        self.assertNotIn("secret123", sanitized)
        self.assertIn("[redacted]", sanitized)

    def test_positive_limit_validation(self):
        self.assertEqual(bluebubbles.positive_limit("25"), 25)
        with self.assertRaises(Exception):
            bluebubbles.positive_limit("0")
        with self.assertRaises(Exception):
            bluebubbles.positive_limit("-5")
        with self.assertRaises(Exception):
            bluebubbles.positive_limit("1000")

    def test_parser(self):
        parser = bluebubbles.parser()
        args = parser.parse_args(["status"])
        self.assertEqual(args.command, "status")

        args = parser.parse_args(["recent-messages", "--limit", "10", "--attachments"])
        self.assertEqual(args.command, "recent-messages")
        self.assertEqual(args.limit, 10)
        self.assertTrue(args.attachments)


if __name__ == "__main__":
    unittest.main()
