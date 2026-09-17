#!/usr/bin/env python3
import importlib.util
import subprocess
import unittest
from pathlib import Path

SKILL_PY = Path(__file__).resolve().parents[1] / "macos.py"
spec = importlib.util.spec_from_file_location("macos_mod", SKILL_PY)
macos_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(macos_mod)


class TestMacOSAdapter(unittest.TestCase):
    def test_parser_status(self):
        p = macos_mod.parser()
        args = p.parse_args(["status"])
        self.assertEqual(args.command, "status")
        self.assertFalse(args.json)

        args_json = p.parse_args(["status", "--json"])
        self.assertEqual(args_json.command, "status")
        self.assertTrue(args_json.json)

    def test_parser_exec(self):
        p = macos_mod.parser()
        args = p.parse_args(["exec", "echo hello"])
        self.assertEqual(args.command, "exec")
        self.assertEqual(args.cmd, "echo hello")

    def test_parser_which(self):
        p = macos_mod.parser()
        args = p.parse_args(["which", "xcodebuild"])
        self.assertEqual(args.command, "which")
        self.assertEqual(args.binary, "xcodebuild")

    def test_resolve_connection(self):
        mock_env = {
            "MACOS_HOST": "adithyas-macbook-pro.tailea5f21.ts.net",
            "MACOS_USER": "shakstzy",
            "MACOS_KNOWN_HOSTS": "/tmp/known_hosts",
            "MACOS_IDENTITY": "/tmp/id_ed25519",
        }
        conn = macos_mod.resolve_connection(mock_env)
        self.assertEqual(conn["MACOS_HOST"], "adithyas-macbook-pro.tailea5f21.ts.net")
        self.assertEqual(conn["MACOS_USER"], "shakstzy")


if __name__ == "__main__":
    unittest.main()
