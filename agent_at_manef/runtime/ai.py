"""Host-supplied code generation stages data only; no provider or automatic activation."""
import ast
import os
from agent_ssot import core
from .registry import Registry, request_value


def validate_source(source):
    if not isinstance(source, str):
        raise core.Refusal('Generator must return Python source text')
    data = source.encode('utf-8')
    core.checked(data)
    try:
        tree = ast.parse(source, feature_version=(3, 10))
        compile(tree, '<candidate>', 'exec')
    except (SyntaxError, ValueError, RecursionError) as exc:
        raise core.Refusal('Generated Python cannot be parsed') from exc
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'run']
    if len(functions) != 1:
        raise core.Refusal('Candidate needs one top-level run(args) function')
    args = functions[0].args
    if len(args.posonlyargs + args.args) != 1 or args.vararg or args.kwarg or args.kwonlyargs:
        raise core.Refusal('Candidate entrypoint must accept one argument')
    return data


def generate_candidate(request, target, generator, *, apply=False):
    if type(apply) is not bool or not callable(generator):
        raise core.Refusal('Explicit apply and host generator required')
    request = request_value(request)
    target = core.separate(target)
    if target.exists():
        raise core.Refusal('Candidate destination must be new')
    # One callback only, never a repair/retry loop or a provider request in this library.
    data = validate_source(generator(request))
    result = core.fresh(target, {'action.py': data, 'REVIEW.md': b'# Inactive Python candidate\n\nReview code, dependencies, license, effects and argument contract. AST validation is not a sandbox. Register explicitly only after review; generation never executes or changes a runtime manifest.\n'}, apply)
    return {**result, 'status': 'staged' if apply else 'preview', 'ai_calls': 1,
            'source_sha256': core.digest(data), 'registered': False, 'executed': False}


def register_candidate(bundle, source, *, aid, version, command, parameters, required,
                       effects='none', timeout_seconds=5, priority=100, reviewed=False, apply=False):
    """Explicit append-only registration. No imports, execution, replacement or hooks."""
    if type(reviewed) is not bool or type(apply) is not bool or (apply and not reviewed):
        raise core.Refusal('Applied registration requires explicit review')
    root = core.separate(bundle)
    registry = Registry.load(root)
    core.slug(aid)
    data = validate_source(core.read(source).decode('utf-8'))
    if aid in registry.actions:
        raise core.Refusal('Action already registered; use a new ID and review revision changes')
    filename = 'actions/' + aid + '.py'
    destination = root / filename
    core.no_links(destination)
    if destination.exists():
        raise core.Refusal('Action destination already exists')
    manifest = core.read(root / 'runtime.json')
    if core.digest(manifest) != registry.fingerprint:
        raise core.Refusal('Registry changed during registration')
    doc = core.obj(manifest)
    doc['actions'].append({'id': aid, 'version': version, 'file': filename,
        'sha256': core.digest(data), 'parameters': parameters, 'required': required,
        'effects': effects, 'timeout_seconds': timeout_seconds})
    doc['routes'].append({'id': aid, 'priority': priority,
                          'command': command, 'when': {}, 'action': aid})
    rendered = core.json_bytes(doc)
    Registry.from_bytes(root, rendered)
    if apply:
        with core.locked(root):
            if core.read(root / 'runtime.json') != manifest:
                raise core.Refusal('Registry changed after preview')
            core.no_links(destination)
            core.mkdir(destination.parent)
            fd = os.open(destination, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(fd, 'wb') as stream:
                stream.write(data)
            # A publication failure can leave an inactive orphan source for inspection.
            core.atomic(root / 'runtime.json', rendered)
    return {'ok': True, 'mode': 'apply' if apply else 'preview', 'action': aid,
            'source_sha256': core.digest(data), 'registered': apply, 'executed': False,
            'review_required': not reviewed}
