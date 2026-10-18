"""Validate wheel/sdist and a clean offline installation. Never publish a package."""
from __future__ import annotations
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path, PurePosixPath
import platform
import subprocess
import sys
import tarfile
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MAX_BYTES = 16 * 1024 * 1024
MAX_MEMBERS = 2048

def run(command, cwd):
    p = subprocess.run(command, cwd=cwd, capture_output=True, text=True, encoding="utf-8", timeout=90)
    if p.returncode:
        raise RuntimeError("Release subprocess failed: " + str(command[1:3]))
    return p.stdout

def path_ok(name):
    parts = PurePosixPath(name).parts
    if not parts or name.startswith("/") or chr(92) in name or ":" in name or ".." in parts:
        raise ValueError("Unsafe distribution path")
    if any(p.startswith(".env") or p.endswith((".env", ".pem", ".key", ".db", ".sqlite")) for p in parts):
        raise ValueError("Runtime secret file in distribution")
    return parts

def check(dist):
    dist = Path(dist).resolve()
    wheels = list(dist.glob("*.whl")); sources = list(dist.glob("*.tar.gz"))
    if len(wheels) != 1 or len(sources) != 1:
        raise ValueError("Exactly one wheel and one sdist required")
    wheel, sdist = wheels[0], sources[0]
    for p in (wheel, sdist):
        if p.is_symlink() or not p.is_file() or p.stat().st_size > MAX_BYTES:
            raise ValueError("Invalid distribution file")
    modules = {p.relative_to(ROOT).as_posix(): p.read_bytes() for folder in ("agent_ssot", "agent_at_manef") for p in (ROOT / folder).rglob("*.py")}
    with zipfile.ZipFile(wheel) as z:
        entries = z.infolist()
        if len(entries) > MAX_MEMBERS or sum(i.file_size for i in entries) > MAX_BYTES or len({i.filename.casefold() for i in entries}) != len(entries):
            raise ValueError("Wheel exceeds limits or has duplicate paths")
        for i in entries:
            path_ok(i.filename)
            if i.is_dir() or ((i.external_attr >> 16) & 0o170000) == 0o120000:
                raise ValueError("Unsupported wheel member")
            if not (i.filename.startswith(("agent_ssot/", "agent_at_manef/")) or ".dist-info/" in i.filename):
                raise ValueError("Unexpected wheel content")
        for n, b in modules.items():
            if z.read(n) != b:
                raise ValueError("Wheel source mismatch")
        metadata = z.read(next(n for n in z.namelist() if n.endswith(".dist-info/METADATA"))).decode()
        if "Requires-Dist:" in metadata:
            raise ValueError("Unexpected runtime dependency")
    with tempfile.TemporaryDirectory(prefix="agent-release-check-") as td:
        root = Path(td).resolve(); unpack = root / "sdist"; unpack.mkdir()
        with tarfile.open(sdist, "r:gz") as z:
            members = z.getmembers()
            if len(members) > MAX_MEMBERS or sum(i.size for i in members) > MAX_BYTES:
                raise ValueError("Source archive exceeds limits")
            seen = set()
            for i in members:
                parts = path_ok(i.name)
                if i.name.casefold() in seen or not (i.isdir() or i.isfile()):
                    raise ValueError("Duplicate or unsupported source entry")
                seen.add(i.name.casefold()); p = unpack.joinpath(*parts)
                if i.isdir():
                    p.mkdir(parents=True, exist_ok=True)
                else:
                    p.parent.mkdir(parents=True, exist_ok=True)
                    with z.extractfile(i) as stream:
                        p.write_bytes(stream.read())
        roots = [p for p in unpack.iterdir() if p.is_dir()]
        if len(roots) != 1:
            raise ValueError("Source archive must have one root")
        src = roots[0]
        for n, b in modules.items():
            if (src / n).read_bytes() != b:
                raise ValueError("Sdist source mismatch")
        for n in ("README.md", "LICENSE", "docs/library.md", "tests/test_adapters.py", "scripts/release_check.py"):
            if not (src / n).is_file():
                raise ValueError("Incomplete source distribution")
        rebuilt = root / "rebuilt"
        run([sys.executable, "-m", "build", "--wheel", "--no-isolation", "--outdir", str(rebuilt)], src)
        rebuilt_wheels = list(rebuilt.glob("*.whl"))
        if len(rebuilt_wheels) != 1:
            raise ValueError("Sdist failed to rebuild")
        with zipfile.ZipFile(rebuilt_wheels[0]) as z:
            for n, b in modules.items():
                if z.read(n) != b:
                    raise ValueError("Rebuilt source mismatch")
        env = root / "environment"
        run([sys.executable, "-m", "venv", str(env)], root)
        scripts = env / ("Scripts" if os.name == "nt" else "bin")
        python = scripts / ("python.exe" if os.name == "nt" else "python")
        run([str(python), "-m", "pip", "install", "--no-index", "--no-deps", str(wheel)], root)
        run([str(python), "-m", "pip", "check"], root)
        current = json.loads(run([str(python), "-I", "-m", "agent_at_manef", "capabilities"], root))
        legacy = json.loads(run([str(python), "-I", "-m", "agent_ssot", "capabilities"], root))
        if current != legacy or current["core"]["runtime_dependencies"]:
            raise ValueError("Installed aliases differ")
        for name in ("agent-at-manef", "agent-ssot"):
            cmd = scripts / (name + (".exe" if os.name == "nt" else ""))
            if json.loads(run([str(cmd), "capabilities"], root)) != current:
                raise ValueError("Console script mismatch")
        exercise = r'''import json, tempfile
from pathlib import Path
import agent_at_manef, agent_ssot
from agent_at_manef import api
from agent_at_manef.runtime import Runtime, scaffold
from agent_ssot import core
with tempfile.TemporaryDirectory() as td:
    root = Path(td).resolve(); source = root / "canonical"
    bundle = root / "runtime"
    scaffold(bundle, apply=True)
    result = Runtime(bundle).dispatch({"command": "echo", "args": {"text": "installed"}}, execute=True)
    assert result["result"] == {"text": "installed"} and result["ai_calls"] == 0
    core.init(source, True)
    target = root / "view"
    assert api.render(source, target, "generic")["ok"] and not target.exists()
    assert api.render(source, target, "generic", apply=True)["ok"]
    assert api.verify(target)["ok"]
    archive = root / "context.zip"
    assert api.backup(source, archive, apply=True)["ok"]
    assert api.restore(archive, root / "restored", apply=True)["ok"]
    assert api.inspect_workspace(source)["source_fingerprint"] == api.inspect_workspace(root / "restored")["source_fingerprint"]
    assert agent_at_manef.__version__ == agent_ssot.__version__
print(json.dumps({"ok": True}))
'''
        if not json.loads(run([str(python), "-I", "-c", exercise], root))["ok"]:
            raise ValueError("Installed lifecycle failed")
    return {"ok": True, "kind": "agent-at-manef-release-check", "version": current["implementation_version"],
            "artifacts": [{"file": p.name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "bytes": p.stat().st_size} for p in (wheel, sdist)],
            "build_tools": {n: importlib.metadata.version(n) for n in ("build", "setuptools", "wheel")},
            "environment": {"os": platform.system(), "architecture": platform.machine(), "python": platform.python_version()},
            "wheel_installed_offline": True, "sdist_rebuilt_offline": True, "legacy_aliases_equal": True,
            "published": False, "signatures_verified": False, "runtime_accounts_used": False}

def main():
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--dist", required=True)
    args = parser.parse_args(); print(json.dumps(check(args.dist), indent=2))

if __name__ == "__main__":
    main()
