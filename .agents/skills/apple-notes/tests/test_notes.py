#!/usr/bin/env python3
import importlib.util
import unittest
from pathlib import Path

SKILL_PY = Path(__file__).resolve().parents[1] / "notes.py"
spec = importlib.util.spec_from_file_location("notes_mod", SKILL_PY)
notes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(notes)


class TestAppleNotes(unittest.TestCase):
    def test_plaintext(self):
        html = "<div>Hello &amp; welcome</div><div>Line 2&nbsp;extra</div>"
        text = notes.plaintext(html)
        self.assertIn("Hello & welcome", text)
        self.assertIn("Line 2 extra", text)

    def test_require_body(self):
        body = "This is a clean body note."
        self.assertEqual(notes.require_body(body), body)

        with self.assertRaises(notes.NotesError):
            notes.require_body("")  # empty
        with self.assertRaises(notes.NotesError):
            notes.require_body("a" * 8001)  # over 8000 limit

    def test_parser(self):
        parser = notes.parser()
        args = parser.parse_args(["status"])
        self.assertEqual(args.command, "status")

        args = parser.parse_args(["create", "Title", "--body", "Some content", "--folder", "Work"])
        self.assertEqual(args.command, "create")
        self.assertEqual(args.title, "Title")
        self.assertEqual(args.body, "Some content")
        self.assertEqual(args.folder_name, "Work")

        args = parser.parse_args(["delete", "x-coredata://123/ICNote/p1", "--force"])
        self.assertEqual(args.command, "delete")
        self.assertTrue(args.force)


if __name__ == "__main__":
    unittest.main()
