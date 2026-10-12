"""Synthetic library and deployment-declaration regression tests."""
from contextlib import redirect_stdout
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from agent_at_manef import api
from agent_at_manef.__main__ import main as branded_main
from agent_ssot import api as old_api, assessment, core
from agent_ssot.__main__ import main


class AssessmentTests(unittest.TestCase):
    def setUp(self):
        self.requirements = {"schema_version": 1, "required": ["model.tool_calls", "harness.approval_enforcement"], "optional": ["host.process_isolation"]}
        self.target = {"schema_version": 1, "target_id": "synthetic-target", "claims": {
            n: {"status": "supported", "evidence": "Synthetic test reference", "observed_at": "2026-10-11"}
            for n in self.requirements["required"]}}

    def test_supported_declarations_are_not_verified_authority(self):
        result = api.assess(self.requirements, self.target)
        self.assertTrue(result["ok"])
        self.assertTrue(result["compatible_by_declaration"])
        for field in ("runtime_probed", "evidence_verified", "evidence_freshness_checked", "deployment_authorized"):
            self.assertFalse(result[field])

    def test_missing_required_blocks(self):
        self.target["claims"].pop("model.tool_calls")
        self.assertEqual(api.assess(self.requirements, self.target)["blocked_requirements"], ["model.tool_calls"])

    def test_unknown_and_unsupported_required_block(self):
        for status in ("unknown", "unsupported"):
            self.target["claims"]["model.tool_calls"]["status"] = status
            self.assertFalse(api.assess(self.requirements, self.target)["compatible_by_declaration"])

    def test_supported_without_evidence_or_date_blocks(self):
        for key, value in (("evidence", "  "), ("observed_at", None)):
            target = copy.deepcopy(self.target)
            target["claims"]["model.tool_calls"][key] = value
            result = api.assess(self.requirements, target)
            self.assertFalse(result["compatible_by_declaration"])
            self.assertEqual(next(r["status"] for r in result["capabilities"] if r["capability"] == "model.tool_calls"), "unsubstantiated")

    def test_optional_gap_does_not_authorize_or_block(self):
        result = api.assess(self.requirements, self.target)
        self.assertTrue(result["compatible_by_declaration"])
        self.assertEqual(result["capabilities"][1]["required"], False)
        self.assertFalse(result["deployment_authorized"])

    def test_empty_required_set_is_explicit(self):
        self.requirements["required"] = []
        result = api.assess(self.requirements, self.target)
        self.assertEqual(result["required_count"], 0)
        self.assertFalse(result["runtime_probed"])

    def test_duplicate_overlap_and_invalid_names_refused(self):
        for names in (["model.tool_calls", "model.tool_calls"], ["host.process_isolation"], ["vendor"], [1]):
            r = copy.deepcopy(self.requirements)
            r["required"] = names
            with self.assertRaises(core.Refusal):
                api.assess(r, self.target)

    def test_schema_types_extra_fields_and_status_refused(self):
        for value in (True, 2, "1", None):
            t = copy.deepcopy(self.target)
            t["schema_version"] = value
            with self.assertRaises(core.Refusal):
                api.assess(self.requirements, t)
        t = copy.deepcopy(self.target)
        t["claims"]["model.tool_calls"]["status"] = "probably"
        with self.assertRaises(core.Refusal):
            api.assess(self.requirements, t)
        t = copy.deepcopy(self.target)
        t["extra"] = True
        with self.assertRaises(core.Refusal):
            api.assess(self.requirements, t)

    def test_invalid_dates_and_claim_shape_refused(self):
        for value in ("2026-02-31", "20261011", 7, "2026-10-11T00:00:00Z"):
            t = copy.deepcopy(self.target)
            t["claims"]["model.tool_calls"]["observed_at"] = value
            with self.assertRaises(core.Refusal):
                api.assess(self.requirements, t)
        t = copy.deepcopy(self.target)
        t["claims"]["model.tool_calls"] = True
        with self.assertRaises(core.Refusal):
            api.assess(self.requirements, t)

    def test_size_limits(self):
        r = copy.deepcopy(self.requirements)
        r["required"] = ["model.feature" + str(i) for i in range(assessment.MAX_ITEMS + 1)]
        with self.assertRaises(core.Refusal):
            api.assess(r, self.target)
        t = copy.deepcopy(self.target)
        t["claims"]["model.tool_calls"]["evidence"] = "x" * 70000
        with self.assertRaises(core.Refusal):
            api.assess(self.requirements, t)

    def test_no_reads_and_no_raw_evidence_echo(self):
        with patch.object(Path, "read_bytes", side_effect=AssertionError("No disk read")):
            result = api.assess(self.requirements, self.target)
        self.assertNotIn("Synthetic test reference", json.dumps(result))

    def test_input_not_mutated(self):
        before = copy.deepcopy((self.requirements, self.target))
        api.assess(self.requirements, self.target)
        self.assertEqual((self.requirements, self.target), before)

    def test_cli_reports_incompatibility_with_exit_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp).resolve()
            (p / "r.json").write_text(json.dumps(self.requirements), encoding="utf-8")
            self.target["claims"] = {}
            (p / "t.json").write_text(json.dumps(self.target), encoding="utf-8")
            out = io.StringIO()
            with redirect_stdout(out):
                code = main(["assess", "--requirements", str(p / "r.json"), "--target-profile", str(p / "t.json")])
            self.assertEqual(code, 2)
            self.assertFalse(json.loads(out.getvalue())["compatible_by_declaration"])


class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.source = self.root / "source"
        core.init(self.source, apply=True)

    def test_one_implementation_and_legacy_schema(self):
        self.assertIs(api.render, old_api.render)
        self.assertEqual(api.API_VERSION, 1)
        contract = api.capabilities()
        self.assertEqual(contract["kind"], "agent-ssot-capabilities")
        self.assertEqual(contract["product"]["name"], "Agent@Manef")
        self.assertEqual(contract["canonical_schema_versions"], [1])

    def test_both_clis_return_same_contract(self):
        results = []
        for command in (main, branded_main):
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(command(["capabilities"]), 0)
            results.append(json.loads(out.getvalue()))
        self.assertEqual(results[0], results[1])

    def test_inspection_returns_metadata_not_full_context(self):
        report = api.inspect_workspace(self.source)
        self.assertEqual(report["agents"], ["researcher"])
        self.assertNotIn("charter", report)
        self.assertNotIn("context", report)
        self.assertFalse(report["runtime_verified"])

    def test_preview_and_legacy_restore(self):
        target = self.root / "output"
        self.assertEqual(api.render(self.source, target, "generic")["mode"], "preview")
        self.assertFalse(target.exists())
        archive = self.root / "old-format.zip"
        core.backup(self.source, archive, apply=True)
        restored = self.root / "restored"
        api.restore(archive, restored)
        self.assertFalse(restored.exists())
        api.restore(archive, restored, apply=True)
        self.assertEqual(core.load_workspace(restored)[1], core.load_workspace(self.source)[1])
        api.render(restored, target, "generic", apply=True)
        self.assertTrue(api.verify(target)["ok"])

    def test_string_apply_is_refused(self):
        for value in ("false", "true", 1, None):
            with self.assertRaises(core.Refusal):
                api.render(self.source, self.root / "out", "generic", apply=value)
            with self.assertRaises(core.Refusal):
                api.backup(self.source, self.root / "archive.zip", apply=value)
        self.assertFalse((self.root / "out").exists())

    def test_same_existing_conflict_guard(self):
        target = self.root / "out"
        api.render(self.source, target, "generic", apply=True)
        edited = target / "agents/researcher/AGENTS.md"
        edited.write_text("Preserve local work", encoding="utf-8")
        with self.assertRaises(core.Refusal):
            api.render(self.source, target, "generic", apply=True)
        self.assertEqual(edited.read_text(encoding="utf-8"), "Preserve local work")


if __name__ == "__main__":
    unittest.main()
