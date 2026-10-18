"""Synthetic runtime contracts; no provider requests or real account data."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
from agent_ssot import core
from agent_at_manef.runtime import Runtime, scaffold
from agent_at_manef.runtime import executor
from agent_at_manef.runtime.ai import generate_candidate, register_candidate
from agent_at_manef.runtime.registry import Registry


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.bundle = self.base / 'runtime'
        scaffold(self.bundle, apply=True)
        self.request = {'command': 'echo', 'args': {'text': 'hello'}}

    def manifest(self, change):
        path = self.bundle / 'runtime.json'
        data = core.obj(path.read_bytes())
        change(data)
        path.write_bytes(core.json_bytes(data))

    def replace_code(self, source):
        path = self.bundle / 'actions/echo.py'
        path.write_text(source, encoding='utf-8')
        self.manifest(lambda d: d['actions'][0].update(sha256=core.digest(path.read_bytes())))

    def test_scaffold_preview_and_existing_destination(self):
        target = self.base / 'preview'
        self.assertEqual(scaffold(target)['mode'], 'preview')
        self.assertFalse(target.exists())
        with self.assertRaises(core.Refusal):
            scaffold(self.bundle, apply=True)

    def test_rule_path_never_calls_ai_or_starts_a_process_in_preview(self):
        planner = lambda *args: self.fail('No AI on matched command')
        with patch.object(subprocess, 'Popen', side_effect=AssertionError('No execution')):
            result = Runtime(self.bundle, planner=planner).dispatch(self.request)
        self.assertEqual(result['status'], 'preview')
        self.assertEqual(result['ai_calls'], 0)
        self.assertEqual(result['action'], 'echo')

    def test_real_python_action_and_no_parent_environment(self):
        self.replace_code('import os\ndef run(args):\n    return {"text": args["text"], "inherited": "PROVIDER_API_KEY" in os.environ}\n')
        with patch.dict(os.environ, {'PROVIDER_API_KEY': 'synthetic-canary'}):
            result = Runtime(self.bundle).dispatch(self.request, execute=True)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['result'], {'text': 'hello', 'inherited': False})
        self.assertEqual(result['ai_calls'], 0)

    def test_fallback_once_and_only_for_unmatched_input(self):
        calls = []
        def planner(request, metadata):
            calls.append((request, metadata))
            return {'action': 'echo', 'args': {'text': 'planned'}}
        runtime = Runtime(self.bundle, planner=planner)
        result = runtime.dispatch({'text': 'say planned'}, execute=True)
        self.assertEqual(result['result'], {'text': 'planned'})
        self.assertEqual(result['ai_calls'], 1)
        self.assertEqual(len(calls), 1)
        self.assertNotIn('source', calls[0][1][0])

    def test_unmatched_without_ai_is_explicit(self):
        self.assertEqual(Runtime(self.bundle).dispatch({'text': 'unknown'})['status'], 'unmatched')

    def test_invalid_input_never_reaches_ai(self):
        runtime = Runtime(self.bundle, planner=lambda *a: self.fail('No AI'))
        for request in ({}, {'command': 'echo', 'args': {'text': 1}},
                        {'command': 'echo', 'args': {'text': 'ok', 'extra': True}},
                        {'command': 'echo', 'args': {}, 'extra': True}):
            with self.subTest(request=request):
                self.assertEqual(runtime.dispatch(request)['status'], 'invalid')

    def test_ambiguous_routes_do_not_fall_back(self):
        self.manifest(lambda d: d['routes'].append(dict(d['routes'][0], id='other')))
        runtime = Runtime(self.bundle, planner=lambda *a: self.fail('No AI'))
        self.assertEqual(runtime.dispatch(self.request)['status'], 'ambiguous')

    def test_route_priority_and_conditions_are_stable(self):
        self.manifest(lambda d: d['routes'].append(dict(d['routes'][0], id='specific', priority=200, when={'text': 'hello'})))
        runtime = Runtime(self.bundle)
        self.assertEqual(runtime.dispatch(self.request)['route'], 'specific')
        self.assertEqual(runtime.dispatch({'command': 'echo', 'args': {'text': 'other'}})['route'], 'echo-command')

    def test_known_command_condition_miss_never_reaches_ai(self):
        self.manifest(lambda d: d['routes'][0].update(when={'text': 'only-this'}))
        runtime = Runtime(self.bundle, planner=lambda *a: self.fail('No AI'))
        self.assertEqual(runtime.dispatch(self.request)['status'], 'invalid')

    def test_effect_and_action_policy_apply_to_both_paths(self):
        self.manifest(lambda d: d['actions'][0].update(effects='write'))
        planner = lambda *a: {'action': 'echo', 'args': {'text': 'ok'}}
        for request in (self.request, {'text': 'unknown'}):
            result = Runtime(self.bundle, planner=planner).dispatch(request, execute=True)
            self.assertEqual(result['status'], 'denied')
        self.assertEqual(Runtime(self.bundle, allow_write=True).dispatch(self.request)['status'], 'preview')
        self.assertEqual(Runtime(self.bundle, allowed_actions=[]).dispatch(self.request)['status'], 'denied')

    def test_invalid_ai_plan_is_not_executed_or_retried(self):
        for plan in ({'action': 'missing', 'args': {}}, {'action': 'echo', 'args': {'text': 1}},
                     {'action': 'echo', 'args': {'text': 'x'}, 'source': 'untrusted'}):
            calls = []
            def planner(*args):
                calls.append(1)
                return plan
            with patch.object(subprocess, 'Popen', side_effect=AssertionError('No execution')):
                result = Runtime(self.bundle, planner=planner).dispatch({'text': 'unknown'}, execute=True)
            self.assertEqual(result['status'], 'invalid')
            self.assertEqual(calls, [1])

    def test_action_failure_does_not_trigger_ai_or_retry(self):
        self.replace_code('def run(args):\n    raise RuntimeError("synthetic-private-canary")\n')
        result = Runtime(self.bundle, planner=lambda *a: self.fail('No AI')).dispatch(self.request, execute=True)
        self.assertEqual(result['status'], 'error')
        self.assertNotIn('synthetic-private-canary', json.dumps(result))

    def test_timeout_and_output_limits(self):
        self.replace_code('def run(args):\n    while True:\n        pass\n')
        self.manifest(lambda d: d['actions'][0].update(timeout_seconds=0.15))
        self.assertEqual(Runtime(self.bundle).dispatch(self.request, execute=True)['status'], 'timeout')
        self.replace_code('def run(args):\n    print("x" * 200000)\n    return {}\n')
        self.manifest(lambda d: d['actions'][0].update(timeout_seconds=5))
        self.assertEqual(Runtime(self.bundle).dispatch(self.request, execute=True)['status'], 'output-limit')

    @unittest.skipUnless(os.name == 'posix', 'POSIX group signal fallback')
    def test_refused_group_signal_still_kills_and_reaps_owned_child(self):
        process = Mock(pid=12345)
        process.poll.return_value = None
        with patch.object(executor.os, 'killpg', side_effect=PermissionError('synthetic refusal')):
            executor._stop(process)
        process.kill.assert_called_once_with()
        process.wait.assert_called_once_with(timeout=5)

    def test_changed_code_is_refused_before_process_launch(self):
        runtime = Runtime(self.bundle)
        (self.bundle / 'actions/echo.py').write_text('raise RuntimeError("never execute")\n')
        with patch.object(subprocess, 'Popen', side_effect=AssertionError('No execution')):
            self.assertEqual(runtime.dispatch(self.request, execute=True)['status'], 'integrity-error')

    def test_registry_does_not_read_python_until_action_selected(self):
        real_read = core.read
        reads = []
        def read(path, **kwargs):
            reads.append(Path(path).suffix)
            return real_read(path, **kwargs)
        with patch.object(core, 'read', side_effect=read):
            runtime = Runtime(self.bundle)
            runtime.dispatch({'text': 'unknown'})
        self.assertNotIn('.py', reads)

    def test_registry_reload_is_explicit_and_atomic(self):
        runtime = Runtime(self.bundle)
        self.manifest(lambda d: d['routes'][0].update(command='say'))
        self.assertEqual(runtime.dispatch(self.request)['status'], 'preview')
        runtime.reload()
        self.assertEqual(runtime.dispatch(self.request)['status'], 'unmatched')
        (self.bundle / 'runtime.json').write_text('{}')
        with self.assertRaises(core.Refusal):
            runtime.reload()
        self.assertEqual(runtime.dispatch({'command': 'say', 'args': {'text': 'ok'}})['status'], 'preview')

    def test_manifest_paths_types_duplicates_and_versions_fail_closed(self):
        path = self.bundle / 'runtime.json'
        original = path.read_bytes()
        changes = [lambda d: d.update(schema_version=True),
                   lambda d: d['actions'][0].update(file='../escape.py'),
                   lambda d: d['actions'][0].update(timeout_seconds=True),
                   lambda d: d['actions'].append(copy.deepcopy(d['actions'][0])),
                   lambda d: d['routes'][0].update(priority=True)]
        for change in changes:
            path.write_bytes(original)
            self.manifest(change)
            with self.assertRaises(core.Refusal):
                Registry.load(self.bundle)

    def test_generated_python_is_staged_without_registration_or_execution(self):
        target = self.base / 'candidate'
        source = 'def run(args):\n    return {"text": args["text"]}\n'
        calls = []
        def generator(request):
            calls.append(request)
            return source
        before = (self.bundle / 'runtime.json').read_bytes()
        with patch.object(subprocess, 'Popen', side_effect=AssertionError('No execution')):
            preview = generate_candidate({'text': 'new capability'}, target, generator)
            self.assertFalse(target.exists())
            result = generate_candidate({'text': 'new capability'}, target, generator, apply=True)
        self.assertEqual(preview['status'], 'preview')
        self.assertEqual(result['status'], 'staged')
        self.assertEqual((target / 'action.py').read_text(), source)
        self.assertEqual((self.bundle / 'runtime.json').read_bytes(), before)
        self.assertEqual(len(calls), 2)

    def test_cli_real_flow(self):
        process = subprocess.run([sys.executable, '-m', 'agent_at_manef.runtime', 'run',
            '--bundle', str(self.bundle), '--request', json.dumps(self.request), '--execute'],
            capture_output=True, timeout=20)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(json.loads(process.stdout)['result'], {'text': 'hello'})

    def test_candidate_registration_preview_review_and_execution(self):
        source = self.base / 'candidate.py'
        source.write_text('def run(args):\n    return {"value": args["value"] * 2}\n')
        kwargs = dict(aid='double', version='1.0.0', command='double',
                      parameters={'value': 'integer'}, required=['value'])
        before = (self.bundle / 'runtime.json').read_bytes()
        with patch.object(subprocess, 'Popen', side_effect=AssertionError('Registration never executes')):
            register_candidate(self.bundle, source, **kwargs)
            self.assertEqual((self.bundle / 'runtime.json').read_bytes(), before)
            with self.assertRaises(core.Refusal):
                register_candidate(self.bundle, source, apply=True, **kwargs)
            register_candidate(self.bundle, source, reviewed=True, apply=True, **kwargs)
        result = Runtime(self.bundle).dispatch({'command': 'double', 'args': {'value': 3}}, execute=True)
        self.assertEqual(result['result'], {'value': 6})
        self.assertEqual(result['ai_calls'], 0)
        with self.assertRaises(core.Refusal):
            register_candidate(self.bundle, source, reviewed=True, apply=True, **kwargs)

    def test_generator_rejects_invalid_code_without_staging(self):
        for source in ('def run(args):\n    return 1\nreturn 2\n', 'def unrelated():\n    pass\n', 'def run(a, b):\n    pass\n'):
            target = self.base / 'invalid-candidate'
            with self.assertRaises(core.Refusal):
                generate_candidate({'text': 'new'}, target, lambda request: source, apply=True)
            self.assertFalse(target.exists())

    def test_registry_metadata_cannot_be_mutated(self):
        registry = Registry.load(self.bundle)
        with self.assertRaises(TypeError):
            registry.actions['echo'].parameters['text'] = 'integer'
        metadata = registry.summaries()
        metadata[0]['parameters']['text'] = 'integer'
        self.assertEqual(registry.actions['echo'].parameters['text'], 'string')

    def test_symlink_action_refused_before_execution(self):
        path = self.bundle / 'actions/echo.py'
        original = self.base / 'original.py'
        path.rename(original)
        try:
            path.symlink_to(original)
        except (OSError, NotImplementedError):
            self.skipTest('Symlinks unavailable')
        with patch.object(subprocess, 'Popen', side_effect=AssertionError('No execution')):
            self.assertEqual(Runtime(self.bundle).dispatch(self.request, execute=True)['status'], 'integrity-error')
