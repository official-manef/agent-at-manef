"""Exercise actual CLI commands with synthetic, disposable source and output."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def run(*args, module='agent_at_manef'):
    process = subprocess.run([sys.executable, '-m', module, *map(str, args)], cwd=ROOT,
                             capture_output=True, text=True, encoding='utf-8', timeout=30)
    if process.returncode:
        raise AssertionError('CLI smoke failed for ' + str(args[0]))
    result = json.loads(process.stdout)
    assert result['ok']
    return result


declaration = run('capabilities')
assert declaration['interface_version'] == 1 and declaration['declaration_only']
assert declaration['readiness']['mso_integration_verified'] is False
catalog_report = run('catalog', '--file', ROOT/'examples/catalog.json')
assert catalog_report['installed'] is False and catalog_report['declaration_only']

with tempfile.TemporaryDirectory() as folder:
    base = Path(folder).resolve()
    bundle = base/'runtime'
    run('scaffold', '--target', bundle, module='agent_at_manef.runtime')
    assert not bundle.exists()
    run('scaffold', '--target', bundle, '--apply', module='agent_at_manef.runtime')
    executed = run('run', '--bundle', bundle, '--request', '{"command":"echo","args":{"text":"synthetic"}}',
                   '--execute', module='agent_at_manef.runtime')
    assert executed['result'] == {'text': 'synthetic'} and executed['ai_calls'] == 0
    source = base/'context'
    run('init', '--target', source)
    assert not source.exists()
    run('init', '--target', source, '--apply')
    run('new', '--workspace', source, '--id', 'writer', '--name', 'Writer', '--owner', 'editor',
        '--mission', 'Draft synthetic documentation for review', '--apply')
    run('doctor', '--workspace', source)
    old = base/'old'; old.mkdir(); (old/'SOUL.md').write_text('# Reviewed candidate\n', encoding='utf-8')
    run('inventory', '--source', old)
    run('import', '--workspace', source, '--source', old, '--file', 'SOUL.md', '--agent', 'writer', '--apply')
    for platform in ('generic', 'codex', 'claude', 'gemini', 'hermes', 'grokbot'):
        target = base/platform
        run('render', '--workspace', source, '--target', target, '--platform', platform)
        assert not target.exists()
        run('render', '--workspace', source, '--target', target, '--platform', platform, '--apply')
        second = run('reconcile', '--workspace', source, '--target', target, '--platform', platform, '--apply')
        assert set(second['actions'].values()) == {'unchanged'}
        run('verify', '--target', target)
    run('reconcile', '--workspace', source, '--target', base/'claude', '--platform', 'generic', '--quarantine-stale', '--apply')
    run('backup', '--workspace', source, '--output', base/'backup.zip', '--apply')
    run('restore', '--archive', base/'backup.zip', '--target', base/'restored', '--apply')
    run('doctor', '--workspace', base/'restored')

assessment_run = subprocess.run([sys.executable, '-m', 'agent_at_manef', 'assess',
    '--requirements', 'examples/requirements.json', '--target-profile', 'examples/target-profile.json'],
    cwd=ROOT, capture_output=True, text=True, encoding='utf-8', timeout=30)
assert assessment_run.returncode == 2
assert json.loads(assessment_run.stdout)['deployment_authorized'] is False

print(json.dumps({'ok': True, 'actual_cli_commands': True, 'platforms': 6, 'backup_restore': True,
                  'credentials_used': False, 'native_runtime_executed': False, 'local_python_action_executed': True}))
