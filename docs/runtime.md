# Deterministic-first local actions

[README](../README.md) · [Security](security.md) · [Library](library.md)

The opt-in `agent_at_manef.runtime` module scaffolds and runs small reviewed Python
actions. Context commands and canonical/backup schema v1 remain offline and Markdown-only.
Keep the runtime bundle in a separate directory; executable actions are not silently
included in context backup, imported from Markdown, or registered by platform adapters.
The runtime has no third-party dependency, provider client, login flow or scheduler.

## First run

From the source checkout (or after installing the package):

```sh
python -m agent_at_manef.runtime scaffold --target ../my-runtime
python -m agent_at_manef.runtime scaffold --target ../my-runtime --apply
python -m agent_at_manef.runtime run --bundle ../my-runtime --request '{"command":"echo","args":{"text":"hello"}}'
python -m agent_at_manef.runtime run --bundle ../my-runtime --request '{"command":"echo","args":{"text":"hello"}}' --execute
```

The scaffold contains `runtime.json` and `actions/echo.py`. Preview returns the selected
action, argument plan and source digest without launching Python. Execute returns
`status: success`, `result: {"text": "hello"}` and `ai_calls: 0`.
Existing scaffold destinations are refused. JSON examples use POSIX/PowerShell quoting;
use the Python API for a portable alternative to shell quoting.

## Routing and one AI fallback

Requests have exactly one of these shapes:

```json
{"command":"echo","args":{"text":"hello"}}
```

```json
{"text":"Interpret this new task"}
```

An immutable command index is loaded once per `Runtime` instance. Matching commands
use exact case-sensitive comparisons and optional `when` argument conditions. Higher
integer priority wins; multiple matching routes at the highest priority return
`ambiguous`. Scalar conditions compare type as well as value, so `true` does not match `1`.
Manifest array order is not a tie breaker.
An existing command with no satisfied condition returns `invalid` without consulting AI.

The control flow is matched route, ambiguous result, optional unmatched planner, then
explicit unmatched result. Matched routes never call the planner, including on invalid
arguments, policy denial, integrity failure, timeout or action failure. There are no
automatic execution retries. A host should use idempotency keys for external effects
and decide explicitly whether to retry a failed action.

The optional planner is a synchronous host-supplied callback:

```python
from agent_at_manef.runtime import Runtime

def planner(request, available_actions):
    # Synthetic example. Replace this body with the host's authorized model adapter.
    return {"action": "echo", "args": {"text": "planned"}}

runtime = Runtime("../my-runtime", planner=planner)
result = runtime.dispatch({"text": "say planned"}, execute=True)
assert result["ai_calls"] == 1
```

Only policy-eligible action metadata is passed to the callback, never Python source,
environment credentials or canonical project context. Plans must contain exactly
`action` and `args`; unknown actions, extra fields and invalid argument types refuse.
The same action/effect policy applies to rule and planner paths. No eligible actions
means denial before a planner call. Callback exceptions return `planner-error` without
echoing exception text or retrying. The embedding host owns model authentication,
provider timeouts, token budgets and any additional metadata retrieval. The callback
can run during preview: preview suppresses action execution, not an explicitly
supplied planner. The CLI has no implicit model configuration or provider requests.

## Action and manifest contract

`runtime.json` has exactly `schema_version: 1`, `kind: agent-at-manef-runtime`,
`actions` and `routes`. Action records have exactly these fields:

| Field | Meaning |
|---|---|
| id / version | Unique portable slug and explicit major.minor.patch version |
| file / sha256 | Relative `actions/*.py` source and pinned lowercase SHA-256 |
| parameters / required | Argument names mapped to types, plus required names |
| effects | Declared none, read or write |
| timeout_seconds | Finite number from 0.05 through 60 |

Supported parameter types are string, integer, number, boolean, object and array.
This is a deliberately small top-level type contract, not full JSON Schema. Extra
arguments are refused; nested object/array contents must be finite bounded JSON.
Actions implement `def run(args)` and return JSON-serializable data.

Routes contain exactly `id`, integer `priority`, `command`, scalar `when` conditions
and a registered `action` ID. Inspect the scaffold for a complete valid manifest.
Manifests, requests, planner output and results are bounded to 64 KiB; there are at
most 128 actions/routes and 32 parameters per action. Python source is at most 1 MiB.

The runtime reads only the selected action's source and checks its digest before
preview/execution. It stages the same checked bytes for execution, rather than
reopening the original path in the child. Registry metadata does not import Python.
`runtime.reload()` explicitly validates and swaps a complete manifest snapshot;
a failed reload retains the previous registry. An in-flight request pins one snapshot.
Source changes without a matching reviewed registry revision return `integrity-error`.

## Generate, review, register, reuse

Code generation is an independent host callback and never activates its own output:

```python
from agent_at_manef.runtime.ai import generate_candidate, register_candidate

def generator(request):
    # Synthetic generator; a host can supply an authorized AI implementation here.
    return 'def run(args):\n    return {"value": args["value"] * 2}\n'

generate_candidate({"text": "double an integer"}, "../double-candidate", generator)
generate_candidate({"text": "double an integer"}, "../double-candidate", generator, apply=True)

# After reviewing the source and its declared effects/contract:
register_candidate("../my-runtime", "../double-candidate/action.py",
    aid="double", version="1.0.0", command="double",
    parameters={"value": "integer"}, required=["value"], reviewed=True, apply=True)
```

Generation calls the callback once, checks bounded text and Python syntax/entrypoint,
and stages `action.py` plus review notes into a new directory. It never imports or
executes the candidate. Syntax checks are not a code safety assessment.

Registration defaults to preview. Applied registration requires `reviewed=True`,
or CLI `--reviewed --apply`; this is the operator's review attestation, not an
authenticated reviewer identity. Registration copies source and atomically publishes
the new manifest under a cooperative lock. Existing action IDs/source destinations
are refused; no installed code is overwritten. Publication failure may leave an
inactive orphan source for inspection. Registration never executes an action.
Call `reload()` on an existing runtime after successful registration. The new command
then runs through the deterministic path with zero planner calls.

CLI equivalent:

```sh
python -m agent_at_manef.runtime register --bundle ../my-runtime --source ../double-candidate/action.py --id double --version 1.0.0 --route-command double --parameters '{"value":"integer"}' --required value
python -m agent_at_manef.runtime register --bundle ../my-runtime --source ../double-candidate/action.py --id double --version 1.0.0 --route-command double --parameters '{"value":"integer"}' --required value --reviewed --apply
```

## Execution boundary

Only execute reviewed, trusted code on an owner-controlled host. A fresh Python
process uses `-I -S`, a private staging working directory, no shell, closed stdin,
an allowlisted operational environment, a deadline and bounded stdout/stderr/results.
Parent provider keys, PYTHONPATH and interpreter startup hooks are not inherited.
POSIX process groups are killed on completion/interruption/timeout; Windows guarantees
termination of the direct child only. POSIX file-size limits supplement output checks;
other systems use process/output monitoring. Temporary files are removed normally,
not securely erased. There is no persistent kernel or hidden state shared across tasks.

This is **not an OS sandbox**: same-user Python can access host files, networking and
process APIs. Effects declarations and `allow_write` gate registration metadata, not
individual system calls. The host must supply real container/VM/OS isolation before
executing untrusted generated code. Default policy permits declared none/read actions;
declared writes additionally need `allow_write=True` or `--allow-write`. Pass an explicit
`allowed_actions` list (or repeated `--allow-action`) for narrower action access.

Determinism covers route selection for a pinned manifest and input. Action code can
still use clocks, randomness, mutable external data or side effects, and model output
remains probabilistic. Results include registry/source hashes and action version for
audit and replay; record input/external state privately when reproducibility matters.

## Measure before adding more machinery

```sh
python -m scripts.benchmark_runtime --samples 100
```

The synthetic benchmark reports metadata load, warm matched-preview p50/p95 and actual
fresh-process Python execution p50/p95. It uses zero provider calls. It does not measure
model latency, certify a native Hermes integration or establish a cross-machine SLA.
