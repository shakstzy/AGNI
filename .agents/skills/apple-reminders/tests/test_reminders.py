#!/usr/bin/env python3
import importlib.util
import unittest
from pathlib import Path

SKILL_PY = Path(__file__).resolve().parents[1] / "reminders.py"
spec = importlib.util.spec_from_file_location("reminders_mod", SKILL_PY)
reminders = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reminders)


class TestAppleReminders(unittest.TestCase):
    def test_require_list_name(self):
        self.assertEqual(reminders.require_list_name("Inbox"), "Inbox")
        self.assertEqual(reminders.require_list_name("Today"), "Today")

        with self.assertRaises(reminders.RemindersError):
            reminders.require_list_name("")
        with self.assertRaises(reminders.RemindersError):
            reminders.require_list_name("a" * 81)

    def test_require_reminder_id(self):
        valid = "x-apple-reminder://12345678-ABCD-EF01-2345-6789ABCDEF01"
        self.assertEqual(reminders.require_reminder_id(valid), valid)

        with self.assertRaises(reminders.RemindersError):
            reminders.require_reminder_id("invalid-id")

    def test_parser(self):
        parser = reminders.parser()
        args = parser.parse_args(["status"])
        self.assertEqual(args.command, "status")

        args = parser.parse_args(["capture", "Call doctor", "--notes", "Dr Smith"])
        self.assertEqual(args.command, "capture")
        self.assertEqual(args.title, "Call doctor")
        self.assertEqual(args.notes, "Dr Smith")

        args = parser.parse_args(["promote", "x-apple-reminder://123", "--force"])
        self.assertEqual(args.command, "promote")
        self.assertTrue(args.force)


if __name__ == "__main__":
    unittest.main()
