#!/usr/bin/env python3
import json
import subprocess
import sys
import unittest
from pathlib import Path

LOCAL_DIR = Path(__file__).resolve().parent.parent
FBM_BIN = LOCAL_DIR / "fbm"


class TestFBMCLI(unittest.TestCase):
    def test_bin_executable(self):
        self.assertTrue(FBM_BIN.is_file(), "fbm executable must exist")
        self.assertTrue(os.access(FBM_BIN, os.X_OK), "fbm must be executable")

    def test_help(self):
        res = subprocess.run([str(FBM_BIN), "--help"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("HADES Facebook Marketplace CLI", res.stdout)
        self.assertIn("status", res.stdout)
        self.assertIn("free", res.stdout)
        self.assertIn("search", res.stdout)

    def test_status_json(self):
        res = subprocess.run([str(FBM_BIN), "status", "--json"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertEqual(data.get("mcp_server"), "facebook-marketplace")
        self.assertIn("austin", data.get("supported_metros", []))
        self.assertIn("sf", data.get("supported_metros", []))
        self.assertIn("nyc", data.get("supported_metros", []))

    def test_metros_presence(self):
        sys.path.insert(0, str(LOCAL_DIR / "scripts"))
        from cli import METRO_PRESETS
        for m in ["austin", "sf", "nyc", "la", "miami", "dallas", "seattle"]:
            self.assertIn(m, METRO_PRESETS)
            self.assertIn("lat", METRO_PRESETS[m])
            self.assertIn("lng", METRO_PRESETS[m])


if __name__ == "__main__":
    import os
    unittest.main()
