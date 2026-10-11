"""All fixtures are synthetic. Tests never access real provider credentials or profiles."""
import io
import json
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from agent_ssot import core


class ContextTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.workspace = self.base / "canonical"
        self.target = self.base / "output"
        core.init(self.workspace, True)

    def render(self, platform="generic", **kwargs):
        return core.reconcile(self.workspace, self.target, platform, **kwargs)

    def test_init_preview_has_no_side_effects(self):
        p = self.base / "new"
        core.init(p)
        self.assertFalse(p.exists())

    def test_init_refuses_existing_target(self):
        with self.assertRaises(core.Refusal):
            core.init(self.workspace, True)

    def test_workspace_has_valid_schema(self):
        _, files, agents = core.load_workspace(self.workspace)
        self.assertEqual(set(agents), {"researcher"})
        self.assertEqual(len(files), 5)

    def test_create_agent_and_reject_duplicates(self):
        core.new_agent(self.workspace, "writer", "Writer", "editor", "Draft reviewed content", ["CONTENT_API_KEY"], True)
        _, _, agents = core.load_workspace(self.workspace)
        self.assertEqual(agents['writer']['credential_names'], ["CONTENT_API_KEY"])
        with self.assertRaises(core.Refusal):
            core.new_agent(self.workspace, "writer", "Writer", "editor", "Draft", apply=True)

    def test_new_agent_preview_does_not_create(self):
        core.new_agent(self.workspace, "writer", "Writer", "editor", "Draft")
        self.assertFalse((self.workspace / "agents/writer").exists())

    def test_reserved_and_unsafe_slugs(self):
        for name in ("CON", "con", "../x", "default", "-unsafe", "x/y", "lpt1", "bad space", "a"*49):
            with self.subTest(name=name), self.assertRaises(core.Refusal):
                core.slug(name)

    def test_empty_owner_rejected(self):
        with self.assertRaises(core.Refusal):
            core.new_agent(self.workspace, "writer", "Writer", "", "Draft", apply=True)
        self.assertFalse((self.workspace / 'agents/writer').exists())

    def test_credential_value_not_accepted_as_name(self):
        with self.assertRaises(core.Refusal):
            core.new_agent(self.workspace, "writer", "Writer", "owner", "Draft", ["TOKEN=value"], True)

    def test_unknown_agent_schema_rejected(self):
        p = self.workspace / "agents/researcher/agent.json"
        data = json.loads(p.read_text()); data['extra'] = 'not allowed'
        p.write_text(json.dumps(data))
        with self.assertRaises(core.Refusal):
            core.load_workspace(self.workspace)

    def test_orphan_context_rejected(self):
        p = self.workspace / "agents/orphan/context.md"; p.parent.mkdir(); p.write_text('orphan')
        with self.assertRaises(core.Refusal):
            core.load_workspace(self.workspace)

    def test_secret_pattern_is_not_echoed(self):
        value = 'password=' + 'synthetic-only-value'
        with self.assertRaises(core.Refusal) as err:
            core.checked(value.encode())
        self.assertNotIn('synthetic-only-value', str(err.exception))

    def test_credential_files_rejected_by_workspace(self):
        for name in ('.env', 'private.env', 'auth.json', 'state.db', 'cookie.json'):
            p = self.workspace / 'agents/researcher' / name; p.write_text('synthetic')
            with self.assertRaises(core.Refusal):
                core.load_workspace(self.workspace)
            p.unlink()

    def test_all_platform_views_are_valid_and_idempotent(self):
        for platform in core.PLATFORMS:
            with self.subTest(platform=platform):
                dest = self.base / platform
                first = core.reconcile(self.workspace, dest, platform)
                self.assertTrue(first['ok']); self.assertFalse(dest.exists())
                core.reconcile(self.workspace, dest, platform, apply=True)
                second = core.reconcile(self.workspace, dest, platform, apply=True)
                self.assertEqual(set(second['actions'].values()), {'unchanged'})
                self.assertTrue(core.verify(dest)['ok'])

    def test_platform_definitions_have_honest_boundaries(self):
        self.render('claude', apply=True)
        self.assertIn('tools: Read, Grep, Glob', (self.target / '.claude/agents/researcher.md').read_text())
        _, hermes, _ = core.render_files(self.workspace, 'hermes')
        self.assertIn('agents/researcher/SOUL.md', hermes)
        self.assertFalse(any(n.endswith('/.env') for n in hermes))

    def test_unmanaged_collision_refuses_all_writes(self):
        self.target.mkdir(); (self.target / 'START-HERE.md').write_text('local')
        self.assertFalse(self.render()['ok'])
        with self.assertRaises(core.Refusal): self.render(apply=True)
        self.assertFalse((self.target / 'agents').exists())

    def test_local_edit_preserved(self):
        self.render(apply=True)
        p = self.target / 'agents/researcher/AGENTS.md'; p.write_text('my edits')
        with self.assertRaises(core.Refusal): self.render(apply=True)
        self.assertEqual(p.read_text(), 'my edits')

    def test_update_archives_previous_managed_file(self):
        self.render(apply=True)
        p = self.workspace / 'agents/researcher/context.md'; p.write_text('# Reviewed new context\n')
        result = self.render(apply=True)
        history = self.target / result['history_directory']
        self.assertTrue(history.exists())
        self.assertTrue(core.verify(self.target)['ok'])
        self.assertIn('Record purpose', (history / 'agents/researcher/context/agents/researcher/context.md').read_text())

    def test_stale_cleanup_is_reversible(self):
        self.render('claude', apply=True)
        result = self.render('generic', apply=True, quarantine=True)
        self.assertFalse((self.target / '.claude/agents/researcher.md').exists())
        self.assertTrue((self.target / result['history_directory'] / '.claude/agents/researcher.md').exists())
        self.assertTrue(core.verify(self.target)['ok'])

    def test_stale_without_quarantine_retained(self):
        self.render('claude', apply=True)
        self.render('generic', apply=True)
        self.assertTrue((self.target / '.claude/agents/researcher.md').exists())

    def test_modified_stale_file_is_never_quarantined(self):
        self.render('claude', apply=True)
        p = self.target / '.claude/agents/researcher.md'; p.write_text('locally owned')
        with self.assertRaises(core.Refusal): self.render('generic', apply=True, quarantine=True)
        self.assertTrue(p.exists())

    def test_unrelated_files_are_not_read_or_modified(self):
        self.target.mkdir(); p = self.target / '.env'; p.write_text('synthetic-secret')
        real = core.read
        def guarded(path, **kw):
            if Path(path) == p: raise AssertionError('Private env read')
            return real(path, **kw)
        with patch.object(core, 'read', side_effect=guarded):
            self.render(apply=True); core.verify(self.target)
        self.assertEqual(p.read_text(), 'synthetic-secret')

    def test_active_lock_retained(self):
        self.target.mkdir(); lock = self.target / core.LOCK; lock.write_text('owner')
        with self.assertRaises(core.Refusal): self.render(apply=True)
        self.assertTrue(lock.exists())

    def test_source_target_overlap_refused(self):
        for dest in (self.workspace, self.workspace/'child', self.base):
            with self.assertRaises(core.Refusal):
                core.reconcile(self.workspace, dest, 'generic', apply=True)

    def test_global_config_target_refused(self):
        for name in ('.HERMES', '.ssh', '.codex', '.claude', '.gemini'):
            with self.assertRaises(core.Refusal):
                core.reconcile(self.workspace, self.base/name, 'generic', apply=True)

    def test_state_cannot_target_secrets_or_history(self):
        self.render(apply=True); p = self.target/core.STATE
        original = json.loads(p.read_text())
        for bad in ('.env', '../other', '.ssot-history/secret.md', 'agents/researcher/.env'):
            altered = json.loads(json.dumps(original)); altered['files'][bad] = '0'*64
            p.write_text(json.dumps(altered))
            with self.assertRaises(core.Refusal): core.verify(self.target)
        p.write_text(json.dumps(original))

    def test_verify_requires_state(self):
        with self.assertRaises(core.Refusal): core.verify(self.target)

    def test_verify_detects_missing_file(self):
        self.render(apply=True); (self.target/'START-HERE.md').unlink()
        self.assertFalse(core.verify(self.target)['ok'])

    def test_inventory_never_reads_private_stores(self):
        source = self.base/'native'; source.mkdir()
        (source/'SOUL.md').write_text('# Identity\n')
        (source/'AGENTS.md').write_text('# Identity\n')
        (source/'.env').write_text('private')
        (source/'config.yaml').write_text('private')
        result = core.inventory(source)
        self.assertEqual(len(result['files']), 2)
        self.assertEqual(len(result['identical_content_groups']), 1)
        self.assertFalse(result['private_stores_read'])

    def test_missing_inventory_source_is_not_an_empty_success(self):
        with self.assertRaises(core.Refusal):
            core.inventory(self.base/'missing')

    def test_non_directory_output_parent_refused_before_writes(self):
        self.target.mkdir()
        (self.target/'agents').write_text('existing user file')
        with self.assertRaises(core.Refusal):
            self.render(apply=True)
        self.assertFalse((self.target/'START-HERE.md').exists())

    def test_import_stages_not_promotes(self):
        source = self.base/'native'; source.mkdir(); (source/'SOUL.md').write_text('# Candidate\n')
        before = (self.workspace/'agents/researcher/AGENT.md').read_bytes()
        core.import_context(self.workspace, source, 'SOUL.md', 'researcher', apply=True)
        self.assertEqual((self.workspace/'agents/researcher/AGENT.md').read_bytes(), before)
        self.assertEqual(len(list((self.workspace/'inbox').iterdir())), 1)
        _, files, _ = core.load_workspace(self.workspace)
        self.assertFalse(any(n.startswith('inbox') for n in files))

    def test_import_preview_does_not_stage(self):
        source = self.base/'native'; source.mkdir(); (source/'SOUL.md').write_text('# Candidate\n')
        core.import_context(self.workspace, source, 'SOUL.md', 'researcher')
        self.assertFalse((self.workspace/'inbox').exists())

    def test_import_disallows_sensitive_paths(self):
        for name in ('.env', 'sessions/notes.md', '../escape.md', 'config.yaml', 'service-account.json'):
            with self.assertRaises(core.Refusal):
                core.import_context(self.workspace, self.base, name, 'researcher', apply=True)

    def test_backup_restore_roundtrip(self):
        archive = self.base/'backup.zip'
        core.backup(self.workspace, archive); self.assertFalse(archive.exists())
        core.backup(self.workspace, archive, True)
        destination = self.base/'restored'
        core.restore(archive, destination); self.assertFalse(destination.exists())
        core.restore(archive, destination, True)
        self.assertEqual(core.load_workspace(self.workspace)[1], core.load_workspace(destination)[1])
        for platform in core.PLATFORMS:
            self.assertTrue(core.reconcile(destination, self.base/f'restored-{platform}', platform, apply=True)['ok'])

    def test_backup_never_includes_raw_inbox(self):
        p = self.workspace/'inbox/raw.md'; p.parent.mkdir(); p.write_text('private review material')
        archive = self.base/'backup.zip'; core.backup(self.workspace, archive, True)
        with zipfile.ZipFile(archive) as z:
            self.assertFalse(any(n.startswith('inbox/') for n in z.namelist()))

    def test_backup_does_not_overwrite(self):
        p = self.base/'backup.zip'; p.write_bytes(b'keep')
        with self.assertRaises(core.Refusal): core.backup(self.workspace, p, True)
        self.assertEqual(p.read_bytes(), b'keep')

    def malicious_zip(self, name, data=b'x', mode=None):
        p = self.base/'bad.zip'
        with zipfile.ZipFile(p, 'w') as z:
            i = zipfile.ZipInfo(name)
            if mode is not None: i.external_attr = mode << 16
            z.writestr(i, data)
            z.writestr('bundle.json', core.json_bytes({'schema_version':1, 'kind':'agent-ssot-context-backup', 'files':{name:{'size':len(data),'sha256':core.digest(data)}}}))
        return p

    def test_zip_traversal_and_private_entries_refused(self):
        for name in ('../escape', '/absolute', 'C:/escape', 'agents/researcher/.env', 'sessions/data.md'):
            p = self.malicious_zip(name)
            with self.assertRaises(core.Refusal): core.restore(p, self.base/'restored', True)
            self.assertFalse((self.base/'restored').exists())

    def test_zip_symlink_refused(self):
        p = self.malicious_zip('agents/researcher/AGENT.md', mode=stat.S_IFLNK|0o777)
        with self.assertRaises(core.Refusal): core.restore(p, self.base/'restored', True)

    def test_zip_checksum_mismatch_refused(self):
        p = self.malicious_zip('workspace.json', b'{}')
        data = io.BytesIO()
        with zipfile.ZipFile(data, 'w') as z:
            z.writestr('workspace.json', b'{}')
            z.writestr('bundle.json', core.json_bytes({'schema_version':1,'kind':'agent-ssot-context-backup','files':{'workspace.json':{'size':2,'sha256':'0'*64}}}))
        p.write_bytes(data.getvalue())
        with self.assertRaises(core.Refusal): core.restore(p, self.base/'restored')

    def test_zip_duplicate_entries_refused(self):
        p = self.base/'duplicates.zip'
        with zipfile.ZipFile(p, 'w') as z:
            z.writestr('AGENT.md', 'one'); z.writestr('agent.md', 'two'); z.writestr('bundle.json', '{}')
        with self.assertRaises(core.Refusal): core.restore(p, self.base/'restored')

    def test_zip_declared_size_limit(self):
        p = self.malicious_zip('agents/researcher/AGENT.md', b'a'*(core.MAX_FILE+1))
        with self.assertRaises(core.Refusal): core.restore(p, self.base/'restored')

    def test_restore_refuses_existing_target(self):
        p = self.base/'backup.zip'; core.backup(self.workspace, p, True)
        with self.assertRaises(core.Refusal): core.restore(p, self.workspace, True)

    def test_duplicate_json_key_rejected(self):
        with self.assertRaises(core.Refusal): core.obj('{"x":1,"x":2}')

    def test_symlink_source_and_target_refused(self):
        alias = self.base/'alias'
        try: alias.symlink_to(self.workspace, target_is_directory=True)
        except (OSError, NotImplementedError): self.skipTest('Symlinks unavailable')
        with self.assertRaises(core.Refusal): core.load_workspace(alias)
        with self.assertRaises(core.Refusal): core.reconcile(self.workspace, alias/'out', 'generic', apply=True)

    def test_cli_error_does_not_echo_secret(self):
        r = subprocess.run([sys.executable, '-m', 'agent_ssot', 'import', '--workspace', str(self.workspace), '--source', str(self.base), '--file', '.env', '--agent', 'researcher'], capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertFalse(json.loads(r.stderr)['ok'])


if __name__ == '__main__':
    unittest.main()
