"""Synthetic contracts: no model, host account, network or native runtime required."""
import ast
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from agent_ssot import capabilities, core
from agent_ssot.__main__ import main

ROOT = Path(__file__).resolve().parents[1]


class PortabilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.source = self.base / "private canonical source"
        core.init(self.source, apply=True)

    def test_capability_schema_and_implementation_agree(self):
        data = capabilities.describe()
        self.assertEqual(data["kind"], "agent-ssot-capabilities")
        self.assertEqual(data["interface_version"], 1)
        self.assertEqual(data["canonical_schema_versions"], [core.VERSION])
        self.assertEqual(data["backup_schema_versions"], [core.VERSION])
        self.assertEqual([a["id"] for a in data["adapters"]], list(core.PLATFORMS))

    def test_capabilities_does_not_open_workspace_or_run_programs(self):
        with patch.object(core, "load_workspace", side_effect=AssertionError("No workspace read")), \
                patch.object(Path, "read_bytes", side_effect=AssertionError("No file read")), \
                patch.object(subprocess, "run", side_effect=AssertionError("No child process")):
            data = capabilities.describe()
        self.assertTrue(data["declaration_only"])
        self.assertTrue(all(v is False for v in data["readiness"].values()))
        self.assertEqual(data["core"]["runtime_dependencies"], [])

    def test_capabilities_ignore_parent_credentials_and_host(self):
        expected = capabilities.describe()
        with patch.dict(os.environ, {"API_KEY": "synthetic-value", "HOME": "/not-real", "MODEL": "test-model", "CLOUD_PROVIDER": "fixture"}, clear=True):
            self.assertEqual(capabilities.describe(), expected)

    def test_capabilities_cli_json_and_no_written_files(self):
        before = {p.relative_to(self.base) for p in self.base.rglob("*")}
        stream = io.StringIO()
        with redirect_stdout(stream):
            self.assertEqual(main(["capabilities"]), 0)
        self.assertEqual(json.loads(stream.getvalue()), capabilities.describe())
        self.assertEqual({p.relative_to(self.base) for p in self.base.rglob("*")}, before)

    def test_mutations_remain_preview_first(self):
        declared = capabilities.describe()["commands"]
        for name in ("init", "new", "import", "render", "reconcile", "backup", "restore"):
            self.assertEqual(declared[name], {"mutating": True, "default_mode": "preview", "apply_flag": "--apply"})
        for name in ("capabilities", "doctor", "inventory", "verify"):
            self.assertFalse(declared[name]["mutating"])

    def test_no_adapter_claims_live_account_or_model_readiness(self):
        for adapter in capabilities.describe()["adapters"]:
            self.assertFalse(adapter["native_registration"])
            self.assertFalse(adapter["model_execution"])
            self.assertFalse(adapter["account_migration"])

    def test_canonical_schema_has_no_required_runtime_fields(self):
        path = self.source / "agents/researcher/agent.json"
        original = json.loads(path.read_text(encoding="utf-8"))
        for key in ("model", "harness", "vm_vendor", "hostname", "api_key"):
            candidate = dict(original)
            candidate[key] = "synthetic"
            path.write_text(json.dumps(candidate), encoding="utf-8")
            with self.assertRaises(core.Refusal):
                core.load_workspace(self.source)
        path.write_text(json.dumps(original), encoding="utf-8")
        self.assertEqual(core.load_workspace(self.source)[2]["researcher"], original)

    def test_identical_canonical_payload_across_six_views(self):
        _, canonical, _ = core.load_workspace(self.source)
        fingerprints = set()
        for platform in core.PLATFORMS:
            _, files, meta = core.render_files(self.source, platform)
            fingerprints.add(meta["source_fingerprint"])
            for name, data in canonical.items():
                if name != "workspace.json":
                    self.assertEqual(files["agents/researcher/context/" + name], data)
        self.assertEqual(len(fingerprints), 1)

    def test_backup_restore_relocation_preserves_rendered_bytes(self):
        archive = self.base / "backup.zip"
        moved = self.base / "different machine" / "restored source"
        core.backup(self.source, archive, apply=True)
        core.restore(archive, moved, apply=True)
        self.assertEqual(core.load_workspace(self.source)[1], core.load_workspace(moved)[1])
        for platform in core.PLATFORMS:
            first = core.render_files(self.source, platform)
            second = core.render_files(moved, platform)
            self.assertEqual(first[1], second[1])
            self.assertEqual(first[2], second[2])

    def test_generated_payload_has_no_implicit_source_absolute_path(self):
        for platform in core.PLATFORMS:
            for data in core.render_files(self.source, platform)[1].values():
                self.assertNotIn(str(self.source).encode(), data)
                self.assertNotIn(str(self.base).encode(), data)

    def test_backup_manifest_contains_relative_names_not_host_paths(self):
        archive = self.base / "backup.zip"
        core.backup(self.source, archive, apply=True)
        with zipfile.ZipFile(archive) as bundle:
            manifest = bundle.read("bundle.json")
            self.assertNotIn(str(self.source).encode(), manifest)
            for name in json.loads(manifest)["files"]:
                self.assertFalse(Path(name).is_absolute())
                self.assertNotIn("..", Path(name).parts)

    def test_requested_unknown_harness_is_not_silently_mapped(self):
        with self.assertRaises(core.Refusal):
            core.render_files(self.source, "future-harness")
        self.assertTrue(core.render_files(self.source, "generic")[1])

    def test_core_imports_no_network_provider_or_process_libraries(self):
        tree = ast.parse((ROOT / "agent_ssot/core.py").read_text(encoding="utf-8"))
        prohibited = {"requests", "httpx", "urllib", "socket", "subprocess", "openai", "anthropic", "google", "boto3", "paramiko"}
        found = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                found.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                found.add((node.module or "").split(".")[0])
        self.assertFalse(found & prohibited)

    def test_rendered_selection_does_not_copy_peer_context(self):
        core.new_agent(self.source, "writer", "Writer", "workspace-owner", "Edit reviewed text.", apply=True)
        for platform in core.PLATFORMS:
            files = core.render_files(self.source, platform, ["researcher"])[1]
            self.assertFalse(any("writer" in n for n in files))


if __name__ == "__main__":
    unittest.main()
