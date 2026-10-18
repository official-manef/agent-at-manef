"""Explicit trusted-code execution with pinned bytes, a fresh process and no shell.

Process hygiene is not an OS sandbox. Run untrusted code in a host-provided sandbox.
"""
from importlib import resources
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
from agent_ssot import core
from .registry import MAX_JSON, json_value

MAX_OUTPUT = 65536


def _stop(process):
    try:
        if os.name == 'posix':
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except OSError:
                # Some hosts refuse a group signal while a resource-limited child
                # exits. Always fall back to the owned child and reap its handle.
                if process.poll() is None:
                    process.kill()
        elif process.poll() is None:
            process.kill()
    finally:
        process.wait(timeout=5)


def run(source, args, timeout):
    with tempfile.TemporaryDirectory(prefix='agent-action-') as td:
        work = Path(td).resolve()
        core.atomic(work / 'action.py', source)
        core.atomic(work / 'input.json', json_value(args))
        worker = resources.files('agent_at_manef.runtime').joinpath('templates/worker.txt').read_bytes()
        core.atomic(work / 'worker.py', worker)
        env = {k: os.environ[k] for k in ('SystemRoot', 'SYSTEMROOT', 'WINDIR') if k in os.environ}
        env.update(PATH='', HOME=str(work), USERPROFILE=str(work), TMPDIR=str(work),
                   TEMP=str(work), TMP=str(work), LANG='C', LC_ALL='C')
        options = {'start_new_session': True} if os.name == 'posix' else {'creationflags': subprocess.CREATE_NO_WINDOW}
        with (work / 'stdout').open('wb') as out, (work / 'stderr').open('wb') as err:
            process = subprocess.Popen([sys.executable, '-I', '-S', str(work / 'worker.py'), str(MAX_OUTPUT)],
                cwd=work, env=env, stdin=subprocess.DEVNULL, stdout=out, stderr=err, **options)
            status = None
            deadline = time.monotonic() + timeout
            try:
                while process.poll() is None:
                    if any((work / n).stat().st_size > MAX_OUTPUT for n in ('stdout', 'stderr', 'result.json') if (work / n).exists()):
                        status = 'output-limit'
                        break
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        status = 'timeout'
                        break
                    try:
                        process.wait(timeout=min(remaining, 0.01))
                    except subprocess.TimeoutExpired:
                        pass
            finally:
                # Kill the process group even if the parent exited and left children.
                _stop(process)
        if status:
            return {'status': status}
        if any((work / n).stat().st_size > MAX_OUTPUT for n in ('stdout', 'stderr', 'result.json') if (work / n).exists()):
            return {'status': 'output-limit'}
        if process.returncode or not (work / 'result.json').is_file():
            return {'status': 'output-limit' if process.returncode == 72 else 'error'}
        data = core.read(work / 'result.json', scan=False)
        if len(data) > MAX_JSON:
            return {'status': 'output-limit'}
        try:
            result = core.obj(data)
            json_value(result)
        except (ValueError, TypeError):
            return {'status': 'error'}
        return {'status': 'success', 'result': result}
