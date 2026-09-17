#!/usr/bin/env python3
import importlib.util
import unittest
from pathlib import Path

SKILL_PY = Path(__file__).resolve().parents[1] / "contacts.py"
spec = importlib.util.spec_from_file_location("contacts_mod", SKILL_PY)
contacts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contacts)


class TestMacOSContacts(unittest.TestCase):
    def test_normalize_phone(self):
        self.assertEqual(contacts.normalize_phone("5551234567"), "+15551234567")
        self.assertEqual(contacts.normalize_phone("+15551234567"), "+15551234567")
        self.assertEqual(contacts.normalize_phone("(555) 123-4567"), "+15551234567")

        with self.assertRaises(contacts.ContactsError):
            contacts.normalize_phone("123")  # too short
        with self.assertRaises(contacts.ContactsError):
            contacts.normalize_phone("+441234567890")  # non-North American

    def test_applescript_literal(self):
        self.assertEqual(contacts.applescript_literal("hello"), '"hello"')
        self.assertEqual(contacts.applescript_literal('hello "world"'), '"hello \\"world\\""')
        with self.assertRaises(contacts.ContactsError):
            contacts.applescript_literal("")

    def test_parser(self):
        parser = contacts.parser()
        args = parser.parse_args(["status"])
        self.assertEqual(args.command, "status")

        args = parser.parse_args(["find-by-phone", "555-123-4567"])
        self.assertEqual(args.command, "find-by-phone")
        self.assertEqual(args.phone, "555-123-4567")

        args = parser.parse_args(["search", "Arya"])
        self.assertEqual(args.command, "search")
        self.assertEqual(args.query, "Arya")

        args = parser.parse_args(["create", "Alice", "5551234567"])
        self.assertEqual(args.command, "create")
        self.assertEqual(args.first_name, "Alice")
        self.assertEqual(args.phone, "5551234567")


if __name__ == "__main__":
    unittest.main()
