"""Synthetic local latency measurements; no provider or Hermes comparison is implied."""
import argparse
import json
import math
from pathlib import Path
import statistics
import tempfile
import time
from agent_at_manef.runtime import Runtime, scaffold


def distribution(values):
    values = sorted(values)
    return {'p50_ms': round(statistics.median(values), 3),
            'p95_ms': round(values[math.ceil(len(values) * 0.95) - 1], 3)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--samples', type=int, default=100)
    args = parser.parse_args()
    if not 10 <= args.samples <= 1000:
        parser.error('Use 10 to 1000 samples')
    with tempfile.TemporaryDirectory() as td:
        bundle = Path(td).resolve() / 'runtime'
        scaffold(bundle, apply=True)
        started = time.perf_counter()
        runtime = Runtime(bundle)
        metadata_ms = (time.perf_counter() - started) * 1000
        request = {'command': 'echo', 'args': {'text': 'synthetic'}}
        measurements = {}
        for name, count, execute in (('matched_preview', args.samples, False),
                                     ('python_execution', min(args.samples, 20), True)):
            values = []
            for _ in range(count):
                started = time.perf_counter()
                result = runtime.dispatch(request, execute=execute)
                values.append((time.perf_counter() - started) * 1000)
                assert result['ok'] and result['ai_calls'] == 0
            measurements[name] = {'samples': count, **distribution(values)}
        print(json.dumps({'ok': True, 'metadata_load_ms': round(metadata_ms, 3),
            'measurements': measurements, 'provider_calls': 0,
            'notes': 'Local synthetic echo; execution includes a fresh isolated-mode Python process, not an OS sandbox.'}, indent=2))


if __name__ == '__main__':
    main()
