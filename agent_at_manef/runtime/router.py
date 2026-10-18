"""Exact command dispatch. Equal-priority matches fail closed instead of guessing."""
import json


def resolve(registry, request):
    if 'command' not in request:
        return 'unmatched', None
    matches = []
    for route in registry.commands.get(request['command'], ()):
        conditions = json.loads(route.when)
        if all(k in request['args'] and type(request['args'][k]) is type(v) and request['args'][k] == v
               for k, v in conditions.items()):
            matches.append(route)
    if not matches:
        return ('invalid' if request['command'] in registry.commands else 'unmatched'), None
    top = matches[0]
    if len(matches) > 1 and matches[1].priority == top.priority:
        return 'ambiguous', None
    return 'matched', top
