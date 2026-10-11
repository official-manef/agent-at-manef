"""Require actual age/minisign binaries and run synthetic recovery acceptance."""
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    missing = [name for name in ("age", "age-keygen", "minisign") if shutil.which(name) is None]
    if missing:
        print(json.dumps({"ok": False, "missing_tools": missing}))
        return 1
    versions = {}
    for name, flag in (("age", "--version"), ("minisign", "-v")):
        result = subprocess.run([name, flag], capture_output=True, text=True, timeout=10)
        if result.returncode:
            return 1
        versions[name] = (result.stdout + result.stderr).strip()[:120]
    result = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests",
                             "-p", "test_secure_transfer.py", "-v"], cwd=ROOT, timeout=90)
    print(json.dumps({"ok": result.returncode == 0, "tool_versions": versions,
                      "keys": "temporary synthetic fixtures", "provider_accounts_used": False,
                      "native_agent_runtime_started": False}))
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
