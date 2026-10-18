"""All fixtures are synthetic. Tests never access real provider credentials or profiles."""
import io
import json
from pathlib import Path
import stat
import struct
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

    def test_new_agent_respects_aggregate_workspace_limits(self):
        original = core.load_workspace(self.workspace)[1]
        addition = core.agent_files('writer', 'Writer', 'owner', 'Write.')
        for apply in (False, True):
            with self.subTest(limit='files', apply=apply):
                with patch.object(core, 'MAX_FILES', len(original) + len(addition) - 1):
                    with self.assertRaises(core.Refusal):
                        core.new_agent(self.workspace, 'writer', 'Writer', 'owner', 'Write.', apply=apply)
            with self.subTest(limit='bytes', apply=apply):
                combined_size = sum(map(len, original.values())) + sum(map(len, addition.values()))
                with patch.object(core, 'MAX_TOTAL', combined_size - 1):
                    with self.assertRaises(core.Refusal):
                        core.new_agent(self.workspace, 'writer', 'Writer', 'owner', 'Write.', apply=apply)
            self.assertFalse((self.workspace / 'agents/writer').exists())
            self.assertEqual(core.load_workspace(self.workspace)[1], original)
        with patch.object(core, 'MAX_FILES', len(original) + len(addition)):
            core.new_agent(self.workspace, 'writer', 'Writer', 'owner', 'Write.', apply=True)
            self.assertIn('writer', core.load_workspace(self.workspace)[2])

    def test_reserved_and_unsafe_slugs(self):
        for name in ("CON", "con", "../x", "default", "-unsafe", "x/y", "lpt1", "bad space", "a"*49):
            with self.subTest(name=name), self.assertRaises(core.Refusal):
                core.slug(name)

    def test_windows_invalid_filename_characters_refused(self):
        for character in '<>"|?*':
            with self.subTest(character=character), self.assertRaises(core.Refusal):
                core.relative('skills/notes' + character + '.md')

    def test_windows_console_device_names_refused(self):
        for name in ('CONIN$.md', 'conout$.md', 'COM¹.md', 'lpt².md', 'com³.md'):
            with self.subTest(name=name), self.assertRaises(core.Refusal):
                core.relative('skills/' + name)

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

    def test_schema_versions_require_integer_one(self):
        for name in ('workspace.json', 'agents/researcher/agent.json'):
            path = self.workspace / name
            original = json.loads(path.read_text())
            for version in (True, 1.0):
                with self.subTest(name=name, version=version):
                    candidate = dict(original, schema_version=version)
                    path.write_text(json.dumps(candidate))
                    with self.assertRaises(core.Refusal):
                        core.load_workspace(self.workspace)
            path.write_text(json.dumps(original))

    def test_canonical_folder_cannot_be_a_file(self):
        for name in ('policies', 'decisions', 'skills'):
            path = self.workspace / name
            if path.exists():
                path.rename(self.workspace / (name + '-saved'))
            path.write_text('context that must not be silently omitted')
            with self.subTest(name=name), self.assertRaises(core.Refusal):
                core.load_workspace(self.workspace)
            path.unlink()

    def test_dangling_canonical_folder_symlink_refused(self):
        alias = self.workspace / 'skills'
        try:
            alias.symlink_to(self.base / 'missing', target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest('Symlinks unavailable')
        with self.assertRaises(core.Refusal):
            core.load_workspace(self.workspace)

    def test_unreadable_canonical_folder_is_not_silently_omitted(self):
        folder = self.workspace / 'skills/reviewed'
        folder.mkdir(parents=True)
        (folder / 'procedure.md').write_text('# Reviewed procedure\n')
        original_scandir = core.os.scandir
        def inaccessible(path):
            if Path(path) == folder:
                raise PermissionError('synthetic inaccessible directory')
            return original_scandir(path)
        with patch.object(core.os, 'scandir', side_effect=inaccessible):
            with self.assertRaises(core.Refusal):
                core.load_workspace(self.workspace)

    def test_canonical_directory_case_aliases_refused(self):
        first = self.workspace / 'skills/Guides/first.md'
        second = self.workspace / 'skills/guides/second.md'
        first.parent.mkdir(parents=True)
        if second.parent.exists():
            self.skipTest('Case-insensitive filesystem')
        second.parent.mkdir()
        first.write_text('# First\n')
        second.write_text('# Second\n')
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

    def test_managed_state_rejects_version_and_path_aliases(self):
        self.render(apply=True)
        path = self.target / core.STATE
        original = json.loads(path.read_text())
        candidates = [dict(original, schema_version=version) for version in (True, 1.0)]
        paths = (
            ('agents/researcher/context/skills/Guides/first.md',
             'agents/researcher/context/skills/guides/second.md'),
            ('agents/researcher/context/skills/guide.md',
             'agents/researcher/context/skills/guide.md/child.md'),
        )
        for first, second in paths:
            candidate = dict(original, files=dict(original['files']))
            candidate['files'].update({first: '0' * 64, second: '0' * 64})
            candidates.append(candidate)
        for candidate in candidates:
            path.write_text(json.dumps(candidate))
            with self.subTest(candidate=candidate), self.assertRaises(core.Refusal):
                core.verify(self.target)
        path.write_text(json.dumps(original))

    def test_empty_selection_never_renders_every_agent(self):
        core.new_agent(self.workspace, 'writer', 'Writer', 'owner', 'Write.', apply=True)
        with self.assertRaises(core.Refusal):
            core.reconcile(self.workspace, self.target, 'generic', selected=[], apply=True)
        self.assertFalse(self.target.exists())

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

    def test_unreadable_inventory_source_is_not_an_empty_success(self):
        with patch.object(core.os, 'scandir', side_effect=PermissionError('synthetic unreadable source')):
            with self.assertRaises(core.Refusal):
                core.inventory(self.workspace)

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
            z.writestr('bundle.json', core.json_bytes({'schema_version':1, 'kind':'agent-ssot-context-backup', 'encrypted':False, 'files':{name:{'size':len(data),'sha256':core.digest(data)}}}))
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
            z.writestr('bundle.json', core.json_bytes({'schema_version':1,'kind':'agent-ssot-context-backup','encrypted':False,'files':{'workspace.json':{'size':2,'sha256':'0'*64}}}))
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

    def test_backup_manifest_schema_is_strict(self):
        valid = self.base / 'backup.zip'
        core.backup(self.workspace, valid, True)
        with zipfile.ZipFile(valid) as archive:
            files = {name: archive.read(name) for name in archive.namelist()}
        original = json.loads(files['bundle.json'])
        candidates = [dict(original, schema_version=version) for version in (True, 1.0)]
        candidates.extend((dict(original, encrypted=True),
                           dict(original, encrypted=0),
                           dict(original, extra='unsupported')))
        record_candidate = json.loads(json.dumps(original))
        record_candidate['files']['workspace.json']['size'] = float(
            record_candidate['files']['workspace.json']['size'])
        candidates.append(record_candidate)
        for candidate in candidates:
            archive = self.base / 'invalid.zip'
            with zipfile.ZipFile(archive, 'w') as bundle:
                for name, data in files.items():
                    bundle.writestr(name, core.json_bytes(candidate) if name == 'bundle.json' else data)
            with self.subTest(candidate=candidate), self.assertRaises(core.Refusal):
                core.restore(archive, self.base / 'restored', True)
            self.assertFalse((self.base / 'restored').exists())

    def test_unsupported_and_corrupt_zip_compression_refused(self):
        valid = self.base / 'valid.zip'
        core.backup(self.workspace, valid, True)
        with zipfile.ZipFile(valid) as bundle:
            entry = bundle.getinfo('bundle.json')
            self.assertEqual(entry.header_offset, 0)
        for mutation in ('unsupported-method', 'invalid-deflate'):
            archive = self.base / (mutation + '.zip')
            data = bytearray(valid.read_bytes())
            if mutation == 'unsupported-method':
                struct.pack_into('<H', data, 8, 99)
                central = data.index(b'PK\x01\x02')
                struct.pack_into('<H', data, central + 10, 99)
            else:
                name_size, extra_size = struct.unpack_from('<HH', data, 26)
                # BTYPE=3 is reserved by DEFLATE and must be refused without a traceback.
                data[30 + name_size + extra_size] = 0x07
            archive.write_bytes(data)
            with self.subTest(mutation=mutation), self.assertRaises(core.Refusal):
                core.restore(archive, self.base / 'restored', True)
            self.assertFalse((self.base / 'restored').exists())

    def test_archive_directory_case_aliases_refused_before_staging(self):
        archive = self.base / 'aliases.zip'
        files = core.load_workspace(self.workspace)[1]
        files.update({'skills/Guides/first.md': b'# First\n',
                      'skills/guides/second.md': b'# Second\n'})
        manifest = {'schema_version': 1, 'kind': 'agent-ssot-context-backup',
                    'encrypted': False,
                    'files': {name: {'size': len(data), 'sha256': core.digest(data)}
                              for name, data in files.items()}}
        with zipfile.ZipFile(archive, 'w') as bundle:
            bundle.writestr('bundle.json', core.json_bytes(manifest))
            for name, data in files.items():
                bundle.writestr(name, data)
        with patch.object(core, 'atomic', side_effect=AssertionError('No staging writes')):
            with self.assertRaises(core.Refusal):
                core.restore(archive, self.base / 'restored', True)
        self.assertFalse((self.base / 'restored').exists())

    def test_bounded_rejects_file_directory_conflicts(self):
        for files in ({'skills/guide.md': b'x', 'skills/guide.md/child.md': b'y'},
                      {'skills/guide.md/child.md': b'y', 'skills/guide.md': b'x'}):
            with self.subTest(files=files), self.assertRaises(core.Refusal):
                core.bounded(files)

    def test_duplicate_json_key_rejected(self):
        with self.assertRaises(core.Refusal): core.obj('{"x":1,"x":2}')

    def test_deep_json_is_refused_without_recursion_exception(self):
        with self.assertRaises(core.Refusal):
            core.obj('[' * 10000 + '0' + ']' * 10000)

    def test_json_depth_limit_is_explicit_and_preserves_string_values(self):
        for open_value, close_value in (("[", "]"), ('{"nested":', "}")):
            with self.subTest(kind=open_value):
                data = open_value * core.MAX_JSON_DEPTH + '"[{}]"' + close_value * core.MAX_JSON_DEPTH
                self.assertIsNotNone(core.obj(data))
                with self.assertRaises(core.Refusal):
                    core.obj(open_value + data + close_value)
        self.assertEqual(core.obj(b'{"text":"[{}]"}'), {"text": "[{}]"})

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
