"""Separate explicit runtime CLI. AI callbacks belong to the embedding host API."""
import json
import sys
from agent_ssot import core
from agent_ssot.__main__ import RedactingParser
from . import Runtime, scaffold
from .ai import register_candidate


def main(argv=None):
    parser = RedactingParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    new = commands.add_parser('scaffold', help='Preview/generate an independent local Python action bundle')
    new.add_argument('--target', required=True)
    new.add_argument('--apply', action='store_true')
    run = commands.add_parser('run', help='Preview a route; --execute runs reviewed registered Python')
    run.add_argument('--bundle', required=True)
    run.add_argument('--request', required=True, help='Bounded JSON command/args or text request')
    run.add_argument('--execute', action='store_true')
    run.add_argument('--allow-write', action='store_true', help='Permit declared write actions; not an OS sandbox')
    run.add_argument('--allow-action', action='append')
    register = commands.add_parser('register', help='Preview/register one explicitly reviewed Python candidate')
    register.add_argument('--bundle', required=True)
    register.add_argument('--source', required=True)
    register.add_argument('--id', required=True)
    register.add_argument('--version', required=True)
    register.add_argument('--route-command', required=True)
    register.add_argument('--parameters', required=True, help='JSON object mapping argument names to type names')
    register.add_argument('--required', action='append', default=[])
    register.add_argument('--effects', choices=('none', 'read', 'write'), default='none')
    register.add_argument('--timeout', type=float, default=5)
    register.add_argument('--priority', type=int, default=100)
    register.add_argument('--reviewed', action='store_true')
    register.add_argument('--apply', action='store_true')
    args = parser.parse_args(argv)
    try:
        if args.command == 'scaffold':
            result = scaffold(args.target, apply=args.apply)
        elif args.command == 'register':
            result = register_candidate(args.bundle, args.source, aid=args.id, version=args.version,
                command=args.route_command, parameters=core.obj(args.parameters), required=args.required,
                effects=args.effects, timeout_seconds=args.timeout, priority=args.priority,
                reviewed=args.reviewed, apply=args.apply)
        else:
            if len(args.request.encode('utf-8')) > 65536:
                raise core.Refusal('Request exceeds runtime limit')
            result = Runtime(args.bundle, allow_write=args.allow_write,
                allowed_actions=args.allow_action).dispatch(core.obj(args.request), execute=args.execute)
        print(json.dumps(result, ensure_ascii=True, allow_nan=False, indent=2))
        return 0 if result['ok'] else 1
    except (core.Refusal, OSError, ValueError, TypeError, KeyError):
        print(json.dumps({'ok': False, 'status': 'refused', 'error': 'Inspect runtime schema, code digest, review and paths locally.'}), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
