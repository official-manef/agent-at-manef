"""JSON output remains parseable under non-UTF-8 Windows/redirected consoles."""
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]

class CliEncodingTests(unittest.TestCase):
    def check_encoding(self, encoding):
        env = dict(os.environ, PYTHONIOENCODING=encoding)
        expected = json.loads((ROOT / "examples/catalog.json").read_text(encoding="utf-8"))["entries"][0]["title"]
        process = subprocess.run([sys.executable, "-m", "agent_at_manef", "catalog", "--file", "examples/catalog.json"],
                                 cwd=ROOT, env=env, capture_output=True, timeout=20)
        self.assertEqual(process.returncode, 0)
        result = json.loads(process.stdout.decode("ascii"))
        self.assertEqual(result["entries"][0]["title"], expected)
        self.assertTrue(result["ok"])
        self.assertFalse(result["installed"])

    def test_ascii_console(self):
        self.check_encoding("ascii")

    def test_windows_cp1252_console(self):
        self.check_encoding("cp1252")
