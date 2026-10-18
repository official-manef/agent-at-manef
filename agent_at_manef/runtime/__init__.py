"""Opt-in deterministic-first runtime; default context commands never import this."""
from __future__ import annotations

from importlib import resources
import json
from agent_ssot import core
from . import executor, router
from .registry import Registry, fields, request_value


def scaffold(target, *, apply=False):
    if type(apply) is not bool:
        raise core.Refusal('Apply must be an explicit boolean')
    source = resources.files(__package__).joinpath('templates/echo.txt').read_bytes()
    manifest = {'schema_version': 1, 'kind': 'agent-at-manef-runtime', 'actions': [{
        'id': 'echo', 'version': '1.0.0', 'file': 'actions/echo.py', 'sha256': core.digest(source),
        'parameters': {'text': 'string'}, 'required': ['text'], 'effects': 'none', 'timeout_seconds': 5}],
        'routes': [{'id': 'echo-command', 'priority': 100, 'command': 'echo', 'when': {}, 'action': 'echo'}]}
    files = {'runtime.json': core.json_bytes(manifest), 'actions/echo.py': source,
             'README.md': b'# Explicit local action bundle\n\nRun with python -m agent_at_manef.runtime. Execution is preview-first. Review registered code and manifest together; declared effects are not an OS sandbox. Keep this bundle outside the canonical context workspace.\n'}
    return core.fresh(target, files, apply)


class Runtime:
    def __init__(self, bundle, *, planner=None, allow_write=False, allowed_actions=None):
        if type(allow_write) is not bool or (planner is not None and not callable(planner)):
            raise core.Refusal('Explicit runtime policy and callable planner required')
        if allowed_actions is not None:
            if not isinstance(allowed_actions, (list, tuple, frozenset)):
                raise core.Refusal('Action policy must be an explicit ID list')
            for aid in allowed_actions:
                core.slug(aid)
        self._registry = Registry.load(bundle)
        self._planner = planner
        self._allow_write = allow_write
        self._allowed = None if allowed_actions is None else frozenset(allowed_actions)

    def reload(self):
        # Assignment happens only after the new manifest fully passes validation.
        self._registry = Registry.load(self._registry.root)

    def dispatch(self, request, *, execute=False):
        if type(execute) is not bool:
            raise core.Refusal('Execute must be an explicit boolean')
        registry = self._registry  # Pin one revision for the entire request, including AI.
        report = {'ok': False, 'status': 'invalid', 'mode': 'execute' if execute else 'preview',
                  'ai_calls': 0, 'registry_sha256': registry.fingerprint}
        try:
            request = request_value(request)
            status, route = router.resolve(registry, request)
            if status == 'matched':
                plan = {'action': route.action, 'args': request['args']}
                report['route'] = route.id
            elif status in {'ambiguous', 'invalid'}:
                return {**report, 'status': status}
            elif self._planner is not None:
                report['ai_calls'] = 1
                # Only metadata for policy-eligible actions is disclosed to the planner.
                eligible = [aid for aid, a in registry.actions.items()
                            if (self._allowed is None or aid in self._allowed)
                            and (a.effects != 'write' or self._allow_write)]
                if not eligible:
                    return {**report, 'status': 'denied', 'ai_calls': 0}
                try:
                    plan = self._planner(json.loads(json.dumps(request)), registry.summaries(eligible))
                except Exception:
                    return {**report, 'status': 'planner-error'}
            else:
                return {**report, 'status': 'unmatched'}
            fields(plan, {'action', 'args'})
            if not isinstance(plan['action'], str) or plan['action'] not in registry.actions:
                raise core.Refusal('Plan references an unknown action')
            action = registry.actions[plan['action']]
            args = action.arguments(plan['args'])
            report.update(action=action.id, action_version=action.version, source_sha256=action.sha256)
            if (self._allowed is not None and action.id not in self._allowed) or (action.effects == 'write' and not self._allow_write):
                return {**report, 'status': 'denied'}
            try:
                source = registry.source(action)
            except (core.Refusal, OSError):
                return {**report, 'status': 'integrity-error'}
            if not execute:
                return {**report, 'ok': True, 'status': 'preview', 'args': args}
            result = executor.run(source, args, action.timeout_seconds)
            return {**report, **result, 'ok': result['status'] == 'success'}
        except (core.Refusal, ValueError, TypeError, KeyError):
            return report
        except OSError:
            return {**report, 'status': 'error'}
