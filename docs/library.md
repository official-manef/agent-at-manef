# Agent@Manef library

[README](../README.md) · [CLI](cli.md) · [Portability](portability.md)

## Source installation

The distribution is named `agent-at-manef`. Install this reviewed source with
`python -m pip install -e .`. No PyPI or npm publication is implied.
The new Python namespace is `agent_at_manef`; the existing `agent_ssot` namespace remains.
Both `agent-at-manef` and `agent-ssot` commands invoke the same implementation.

```python
from agent_at_manef import api

contract = api.capabilities()
assert api.API_VERSION == contract['library_api_version'] == 1
summary = api.inspect_workspace('../my-agent-context')
plan = api.render('../my-agent-context', '../my-platform-view', 'generic')
assert plan['mode'] == 'preview'
```

The source workspace must already exist. The facade exposes capabilities, assess,
inspect_workspace, render, backup, restore and verify. Rendering, backup and restore
are preview-first; an authorized write requires the keyword argument `apply=True`.
Boolean controls reject strings and integers. Inspection returns IDs, counts and a
source fingerprint instead of the full source text.

For `api.render`, `agents=None` selects every canonical agent. An explicit empty list
is refused rather than expanding its scope. Pass a nonempty list of existing IDs to
prepare a narrower view.

The facade has one implementation, not a copied codebase. The documented API is version 1;
consumers should pin a tested source revision until a reproducible release process exists.
Legacy workspace/backup schema version 1 and managed-state filenames are unchanged.
Product branding does not require rewriting existing archives or user directories.

## Declaration assessment

`api.assess(requirements, target)` compares namespaced capability requirements with
supported, unsupported or unknown declarations. Missing required declarations fail.
Supported entries without an evidence reference and observation date also fail.
The result is planning information: it does not probe the destination, check evidence
truth/freshness, run a model, connect an account, or authorize deployment.

CLI equivalent: `python -m agent_at_manef assess --requirements requirements.json
--target-profile target.json` (one command line). Exit 0 means compatible declarations,
2 means missing/unsupported required capability, and 1 means invalid input.
An empty required set is vacuously compatible; it is not runtime acceptance.

## Release roadmap

Before package publication: confirm registry availability, reproducible wheel/source
builds, release provenance, supported environments and a versioning policy. A future
TypeScript facade should consume the JSON interface before duplicating the implementation.
A future agent/skill catalog should record source, license, digest, required capabilities
and review status. Neither a remote catalog nor an npm package is released here.

MSO is a consumer of the toolkit, not a prerequisite. See the
[consumer contract](integrations/mso.md). Keep execution and operational state in the
host; keep canonical definitions portable and independently usable.

[Detailed assessment schema](assessment.md) and synthetic examples document the comparison contract.

## Catalog metadata

`api.inspect_catalog(path)` validates one explicit local file. It does not authenticate source,
review or install authority. See [catalog](catalog.md) and [release gates](release.md).

## Optional secure transport module

`agent_at_manef.secure_transfer` provides preview-first `encrypt`, `verify` and `restore` wrappers for external age/minisign tools. It is not loaded by the default facade. Read the [security and trust contract](secure-transfer.md) before using its explicit execution flags. Default backup/restore and legacy aliases stay unchanged.

## Reuse a validated context snapshot

`api.prepare_workspace(path)` validates once and returns an immutable in-memory revision.
Pass that snapshot as `api.render(snapshot, target, platform)` for repeated selected-agent
renders without rereading peer context. Edits on disk are observed only after calling
`prepare_workspace` again. Path-based calls retain full fresh validation. Snapshots hold
private context in memory; do not log or publish their contents.

The actual charter generator template is [packaged with the library](../agent_ssot/templates/AGENT.md).
Source and installed-wheel generation use this same file. Existing v1 default output bytes
are preserved. Generated views have separate limits of 4096 files and 64 MiB, with managed
state still bounded to 1 MiB. Canonical/backup limits remain 512 files and 32 MiB.
Shared copies remain self-contained per agent. [Optional runtime](runtime.md) uses its own
bundle schema and explicit module; importing this facade does not load its executor.
