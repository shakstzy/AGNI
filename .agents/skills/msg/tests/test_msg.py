#!/usr/bin/env python3
"""Tests for HADES Unified Messaging Dispatcher (`msg`)."""

import unittest
from unittest.mock import patch
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import msg


class TestMsg(unittest.TestCase):

    def test_detect_channel(self):
        self.assertEqual(msg.detect_channel("@username"), "telegram")
        self.assertEqual(msg.detect_channel("123456@s.whatsapp.net"), "whatsapp")
        self.assertEqual(msg.detect_channel("+15104499964"), "bluebubbles")
        self.assertEqual(msg.detect_channel("5104499964"), "bluebubbles")

    @patch("msg.run_cmd")
    def test_resolve_whatsapp_contact(self, mock_run):
        mock_run.return_value = (
            0,
            '{"success":true,"data":[{"jid":"123@s.whatsapp.net","name":"Mom"}]}',
            "",
        )
        res = msg.resolve_whatsapp_contact("Mom")
        self.assertIsNotNone(res)
        self.assertEqual(res[0], "123@s.whatsapp.net")
        self.assertEqual(res[1], "Mom")

    @patch("msg.run_cmd")
    def test_send_whatsapp(self, mock_run):
        mock_run.return_value = (0, "ok", "")
        ok, text = msg.send_whatsapp("123@s.whatsapp.net", "Hello")
        self.assertTrue(ok)
        self.assertIn("Sent to 123@s.whatsapp.net", text)

    @patch("msg.run_cmd")
    def test_send_bluebubbles(self, mock_run):
        mock_run.return_value = (0, "ok", "")
        ok, text = msg.send_bluebubbles("+15104499964", "Hello")
        self.assertTrue(ok)
        self.assertIn("Sent to +15104499964", text)

    @patch("msg.run_cmd")
    def test_send_telegram(self, mock_run):
        mock_run.return_value = (0, "ok", "")
        ok, text = msg.send_telegram("@shakstzy", "Ping")
        self.assertTrue(ok)
        self.assertIn("Sent to @shakstzy", text)

    @patch("msg.run_cmd")
    def test_check_status(self, mock_run):
        mock_run.side_effect = [
            (0, '{"data":{"authenticated":true}}', ""),
            (0, '{"status": 200}', ""),
            (0, 'Session valid', ""),
        ]
        statuses = msg.check_status()
        self.assertTrue(statuses["whatsapp"]["ok"])
        self.assertTrue(statuses["bluebubbles"]["ok"])
        self.assertTrue(statuses["telegram"]["ok"])


if __name__ == "__main__":
    unittest.main()
