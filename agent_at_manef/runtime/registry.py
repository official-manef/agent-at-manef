"""Bounded immutable action metadata. Python code is read only for a selected action."""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
import re
from types import MappingProxyType
from agent_ssot import core

MAX_JSON = 65536
MAX_ACTIONS = 128
TYPES = {'string': str, 'integer': int, 'number': (int, float),
         'boolean': bool, 'object': dict, 'array': list}


def json_value(value):
    try:
        data = json.dumps(value, ensure_ascii=True, allow_nan=False).encode('ascii')
    except (TypeError, ValueError, RecursionError) as exc:
        raise core.Refusal('Expected bounded finite JSON') from exc
    if len(data) > MAX_JSON:
        raise core.Refusal('Runtime JSON exceeds limit')
    return data


def fields(value, expected):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise core.Refusal('Unknown or missing runtime fields')


def request_value(value):
    json_value(value)
    if isinstance(value, dict) and set(value) == {'text'}:
        if not isinstance(value['text'], str) or not value['text'].strip():
            raise core.Refusal('Text request must be explicit')
    else:
        fields(value, {'command', 'args'})
        if not isinstance(value['command'], str) or not value['command'].strip() or not isinstance(value['args'], dict):
            raise core.Refusal('Invalid command request')
    # Detach callbacks/callers from the request used for authorization and routing.
    return json.loads(json_value(value))


@dataclass(frozen=True)
class Action:
    id: str
    version: str
    file: str
    sha256: str
    parameters: object
    required: tuple
    effects: str
    timeout_seconds: float

    def arguments(self, args):
        json_value(args)
        if not isinstance(args, dict) or set(args) - set(self.parameters) or not set(self.required) <= set(args):
            raise core.Refusal('Invalid action arguments')
        for key, value in args.items():
            kind = self.parameters[key]
            if not isinstance(value, TYPES[kind]) or (kind in {'integer', 'number'} and isinstance(value, bool)):
                raise core.Refusal('Action argument type mismatch')
        return json.loads(json_value(args))


@dataclass(frozen=True)
class Route:
    id: str
    priority: int
    command: str
    when: bytes
    action: str


@dataclass(frozen=True)
class Registry:
    root: Path
    actions: object
    routes: tuple
    commands: object
    fingerprint: str

    @classmethod
    def load(cls, root):
        root = core.location(root)
        data = core.read(root / 'runtime.json')
        return cls.from_bytes(root, data)

    @classmethod
    def from_bytes(cls, root, data):
        if len(data) > MAX_JSON:
            raise core.Refusal('Runtime manifest exceeds limit')
        doc = core.obj(data)
        fields(doc, {'schema_version', 'kind', 'actions', 'routes'})
        if type(doc['schema_version']) is not int or doc['schema_version'] != 1 or doc['kind'] != 'agent-at-manef-runtime':
            raise core.Refusal('Unsupported runtime schema')
        json_value(doc)
        if not isinstance(doc['actions'], list) or not 1 <= len(doc['actions']) <= MAX_ACTIONS:
            raise core.Refusal('Invalid action count')
        actions = {}
        paths = []
        for a in doc['actions']:
            fields(a, {'id', 'version', 'file', 'sha256', 'parameters', 'required', 'effects', 'timeout_seconds'})
            aid = core.slug(a['id'])
            if aid in actions:
                raise core.Refusal('Duplicate action ID')
            if not isinstance(a['version'], str) or not re.fullmatch(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)', a['version']):
                raise core.Refusal('Action version must be major.minor.patch')
            path = core.relative(a['file'])
            if len(path.parts) < 2 or path.parts[0] != 'actions' or path.suffix != '.py':
                raise core.Refusal('Action must be a Python file below actions/')
            paths.append(path.as_posix())
            if not isinstance(a['sha256'], str) or not re.fullmatch('[a-f0-9]{64}', a['sha256']):
                raise core.Refusal('Action source digest required')
            params, required = a['parameters'], a['required']
            if not isinstance(params, dict) or len(params) > 32 or not isinstance(required, list):
                raise core.Refusal('Invalid action parameter contract')
            if any(not isinstance(k, str) or not re.fullmatch('[a-z][a-z0-9_]{0,47}', k)
                   or not isinstance(t, str) or t not in TYPES for k, t in params.items()):
                raise core.Refusal('Unsupported action parameter')
            if any(not isinstance(k, str) or k not in params for k in required) or len(set(required)) != len(required):
                raise core.Refusal('Invalid required parameters')
            if a['effects'] not in ('none', 'read', 'write'):
                raise core.Refusal('Unknown declared effects')
            timeout = a['timeout_seconds']
            if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0.05 <= timeout <= 60:
                raise core.Refusal('Action timeout must be 0.05 to 60 seconds')
            actions[aid] = Action(aid, a['version'], path.as_posix(), a['sha256'],
                                  MappingProxyType(dict(params)), tuple(required), a['effects'], float(timeout))
        core.path_tree(paths)
        if len({p.casefold() for p in paths}) != len(paths):
            raise core.Refusal('Action source aliases refused')
        if not isinstance(doc['routes'], list) or len(doc['routes']) > MAX_ACTIONS:
            raise core.Refusal('Invalid route count')
        routes, seen, commands = [], set(), {}
        for r in doc['routes']:
            fields(r, {'id', 'priority', 'command', 'when', 'action'})
            rid = core.slug(r['id'])
            if rid in seen or type(r['priority']) is not int or not -10000 <= r['priority'] <= 10000:
                raise core.Refusal('Duplicate route or invalid priority')
            seen.add(rid)
            if not isinstance(r['command'], str) or not r['command'].strip() or len(r['command']) > 128:
                raise core.Refusal('Invalid route command')
            if not isinstance(r['action'], str) or r['action'] not in actions:
                raise core.Refusal('Unknown route action')
            if not isinstance(r['when'], dict) or set(r['when']) - set(actions[r['action']].parameters):
                raise core.Refusal('Invalid route conditions')
            # Conditions compare JSON scalars with exact types (True is not 1).
            if any(type(v) not in (str, int, float, bool, type(None)) for v in r['when'].values()):
                raise core.Refusal('Route conditions must be scalars')
            route = Route(rid, r['priority'], r['command'], json_value(r['when']), r['action'])
            routes.append(route)
            commands.setdefault(route.command, []).append(route)
        return cls(root, MappingProxyType(actions), tuple(routes),
                   MappingProxyType({k: tuple(sorted(v, key=lambda r: (-r.priority, r.id))) for k, v in commands.items()}),
                   core.digest(data))

    def summaries(self, allowed=None):
        return [{'id': a.id, 'version': a.version, 'parameters': dict(a.parameters),
                 'required': list(a.required), 'effects': a.effects}
                for aid, a in sorted(self.actions.items()) if allowed is None or aid in allowed]

    def source(self, action):
        data = core.read(self.root / action.file, scan=False)
        if len(data) > core.MAX_FILE or core.digest(data) != action.sha256:
            raise core.Refusal('Selected action source changed')
        return data
