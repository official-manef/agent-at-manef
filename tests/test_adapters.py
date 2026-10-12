"""Synthetic v1 output conformance and registry safety."""
from dataclasses import FrozenInstanceError
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from agent_ssot import adapters, capabilities, core
ROOT = Path(__file__).resolve().parents[1]

class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name).resolve(); self.source = self.base / "source"
        core.init(self.source, True)

    def test_v1_output_bytes_preserved(self):
        expected = json.loads((ROOT / "tests/fixtures/adapter-v1-hashes.json").read_text(encoding="utf-8"))["outputs"]
        for p in core.PLATFORMS:
            self.assertEqual({n: hashlib.sha256(b).hexdigest() for n, b in core.render_files(self.source, p)[1].items()}, expected[p])

    def test_one_registry_for_core_and_capabilities(self):
        self.assertEqual(core.PLATFORMS, tuple(adapters.REGISTRY))
        self.assertEqual(capabilities.describe()["adapters"], adapters.describe())

    def test_registry_is_immutable(self):
        with self.assertRaises(TypeError): adapters.REGISTRY["new"] = adapters.REGISTRY["generic"]
        with self.assertRaises(FrozenInstanceError): adapters.REGISTRY["generic"].id = "new"

    def test_renderers_are_pure_declared_output(self):
        view = adapters.AgentView("sample", "Sample", "Review", b"# Charter\n", b"# Guide\n")
        with patch.object(Path, "read_bytes", side_effect=AssertionError("No reads")), patch.object(Path, "write_bytes", side_effect=AssertionError("No writes")):
            for p, adapter in adapters.REGISTRY.items():
                files = adapters.render(p, view)
                self.assertEqual({n.rsplit("/", 1)[1] for n in files if n.startswith("agents/sample/")}, set(adapter.filenames))
                self.assertTrue(all(core.managed_name(n) and isinstance(b, bytes) for n, b in files.items()))

    def test_unknown_adapter_refused(self):
        with self.assertRaises(ValueError): adapters.render("unknown", adapters.AgentView("sample", "Sample", "Review", b"", b""))
        with self.assertRaises(core.Refusal): core.render_files(self.source, "unknown")

    def test_local_edits_protected_for_each_adapter(self):
        for p in core.PLATFORMS:
            target = self.base / p; core.reconcile(self.source, target, p, apply=True)
            file = target / "agents/researcher/AGENTS.md"; file.write_text("# Local\n", encoding="utf-8")
            self.assertFalse(core.reconcile(self.source, target, p)["ok"])
            with self.assertRaises(core.Refusal): core.reconcile(self.source, target, p, apply=True)
            self.assertEqual(file.read_text(encoding="utf-8"), "# Local\n")

    def test_platform_switch_keeps_history_and_unrelated_files(self):
        target = self.base / "view"; core.reconcile(self.source, target, "hermes", apply=True)
        note = target / "note.txt"; note.write_text("keep", encoding="utf-8")
        report = core.reconcile(self.source, target, "generic", apply=True, quarantine=True)
        self.assertTrue((target / report["history_directory"] / "agents/researcher/SOUL.md").is_file())
        self.assertFalse((target / "agents/researcher/SOUL.md").exists())
        self.assertEqual(note.read_text(encoding="utf-8"), "keep")
        self.assertTrue(core.verify(target)["ok"])

    def test_description_mutation_does_not_change_registry(self):
        data = adapters.describe(); data[0]["id"] = "changed"
        self.assertEqual(adapters.describe()[0]["id"], "generic")
