"""Synthetic catalog safety and non-authority contracts."""
from copy import deepcopy
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from agent_at_manef import api
from agent_ssot import catalog, core
from agent_ssot.__main__ import main
ROOT = Path(__file__).resolve().parents[1]

class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / "examples/catalog.json").read_text(encoding="utf-8"))

    def test_example_is_unverified(self):
        r = catalog.validate(self.data)
        self.assertTrue(r["ok"]); self.assertFalse(r["installed"]); self.assertFalse(r["remote_sources_fetched"])
        self.assertEqual(r["entries"][0]["state"], "draft")
        self.assertTrue(all(r["entries"][0][k] is False for k in ("review_verified", "source_verified", "install_authorized")))

    def test_approved_needs_review_but_grants_no_authority(self):
        e = self.data["entries"][0]; e["state"] = "approved"
        with self.assertRaises(core.Refusal): catalog.validate(self.data)
        e["review"] = {"reviewer": "Example", "reviewed_on": "2026-10-11", "evidence": "https://example.invalid/review"}
        r = catalog.validate(self.data)["entries"][0]
        self.assertTrue(r["review_declared"]); self.assertFalse(r["review_verified"]); self.assertFalse(r["install_authorized"])

    def test_extra_execution_fields_and_invalid_states_refused(self):
        for key, value in (("state", []), ("state", "live"), ("kind", {}), ("kind", "script"), ("hooks", [])):
            d = deepcopy(self.data); d["entries"][0][key] = value
            with self.assertRaises(core.Refusal): catalog.validate(d)

    def test_schema_versions_and_duplicate_identity_refused(self):
        for v in (True, "1", 2):
            d = deepcopy(self.data); d["schema_version"] = v
            with self.assertRaises(core.Refusal): catalog.validate(d)
        self.data["entries"] *= 2
        with self.assertRaises(core.Refusal): catalog.validate(self.data)

    def test_immutable_source_and_safe_url_required(self):
        for key, value in (("revision", "main"), ("sha256", "abc"), ("path", "../.env"), ("repository", "http://example.invalid/r"), ("repository", "https://example.invalid/?token=x")):
            d = deepcopy(self.data); d["entries"][0]["source"][key] = value
            with self.assertRaises(core.Refusal): catalog.validate(d)

    def test_explicit_semver_required(self):
        for v in (None, "latest", "1", "1.2", "01.2.3", "1.2.3+mutable"):
            d = deepcopy(self.data); d["entries"][0]["version"] = v
            with self.assertRaises(core.Refusal): catalog.validate(d)

    def test_capability_and_credential_names_only(self):
        for key, v in (("requirements", ["unknown.foo"]), ("credential_names", ["KEY=value"]), ("requirements", ["host.filesystem"] * 2), ("credential_names", ["KEY"] * 2)):
            d = deepcopy(self.data); d["entries"][0][key] = v
            with self.assertRaises(core.Refusal): catalog.validate(d)

    def test_review_date_and_url_validation(self):
        for when, url in (("2026-02-30", "https://example.invalid/r"), ("yesterday", "https://example.invalid/r"), ("2026-10-11", "file:///secret")):
            d = deepcopy(self.data); d["entries"][0]["review"] = {"reviewer": "Example", "reviewed_on": when, "evidence": url}
            with self.assertRaises(core.Refusal): catalog.validate(d)

    def test_no_sources_read_and_input_unchanged(self):
        original = deepcopy(self.data)
        with patch.object(Path, "read_bytes", side_effect=AssertionError("No source read")): catalog.validate(self.data)
        self.assertEqual(self.data, original)

    def test_size_limit_and_empty_catalog(self):
        d = deepcopy(self.data); d["entries"] *= 129
        with self.assertRaises(core.Refusal): catalog.validate(d)
        d["entries"] = []; self.assertEqual(catalog.validate(d)["entries"], [])

    def test_cli_and_library_agree_without_writes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td).resolve(); p = root / "catalog.json"; p.write_text(json.dumps(self.data), encoding="utf-8")
            original = p.read_bytes(); stream = io.StringIO()
            with redirect_stdout(stream): self.assertEqual(main(["catalog", "--file", str(p)]), 0)
            self.assertEqual(json.loads(stream.getvalue()), api.inspect_catalog(p))
            self.assertEqual(p.read_bytes(), original); self.assertEqual(len(list(root.iterdir())), 1)

    def test_duplicate_json_keys_refused(self):
        with self.assertRaises(core.Refusal): core.obj(b'{"schema_version":1,"schema_version":1}')
