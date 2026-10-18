"""Regressions for generated-view budgets, real templates and reusable snapshots."""
from importlib import resources
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from agent_ssot import core


class RenderScalingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.source = self.base / 'canonical'
        core.init(self.source, True)

    def test_two_agents_with_shared_context_fit_separate_output_budget(self):
        core.new_agent(self.source, 'writer', 'Writer', 'owner', 'Write.', apply=True)
        for i in range(249):
            core.atomic(self.source / f'skills/note-{i:03}.md', b'# Shared\n')
        self.assertEqual(len(core.load_workspace(self.source)[1]), 257)
        target = self.base / 'view'
        self.assertTrue(core.reconcile(self.source, target, 'generic', apply=True)['ok'])
        self.assertEqual(core.verify(target)['managed_files'], 513)
        core.backup(self.source, self.base / 'context.zip', apply=True)
        core.restore(self.base / 'context.zip', self.base / 'restored', apply=True)

    def test_snapshot_reuses_validated_context_without_rereading_peers(self):
        snapshot = core.snapshot(self.source)
        expected = core.render_files(self.source, 'generic')[1]
        core.atomic(self.source / 'agents/researcher/context.md', b'# New revision\n')
        with patch.object(core, 'read', side_effect=AssertionError('Snapshot does no I/O')):
            self.assertEqual(core.render_files(snapshot, 'generic')[1], expected)
        self.assertNotEqual(core.render_files(core.snapshot(self.source), 'generic')[1], expected)

    def test_init_uses_packaged_template_source(self):
        template = resources.files('agent_ssot').joinpath('templates/AGENT.md')
        with patch.object(type(template), 'read_text', return_value='# $name\n\nCustom template.\n'):
            files = core.agent_files('writer', 'Writer', 'owner', 'Write.')
        self.assertEqual(files['agents/writer/AGENT.md'], b'# Writer\n\nCustom template.\n')
