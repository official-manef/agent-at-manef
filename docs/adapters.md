# Reviewed adapter contract

[Platforms](platforms.md) · [Library](library.md) · [Release gate](release.md)

`agent_ssot/adapters.py` holds the single immutable built-in registry. The canonical loader,
filesystem writer, reconciliation and backup remain in core. Renderers receive AgentView data
and return declared relative files without I/O, network, provider clients or runtime execution.
Capabilities and CLI choices derive from the same registry. Unknown adapters are rejected.

New adapters require reviewed source changes, exact filenames, a stated output level and
conformance tests. Do not load arbitrary entry points, Python modules, downloaded plugins or
catalog hooks. Canonical payload and per-agent selection remain owned by core. This is modular
internal architecture, not a secure plugin sandbox or a public extension loader.

`tests/test_adapters.py` checks hashes captured from the prior implementation for all six
outputs, registry immutability, pure rendering, local-edit protection and reversible stale-file
quarantine. Existing tests cover recovery, source relocation and absolute-path exclusion.
Conformance certifies file behavior, not native discovery, authenticated accounts, model
understanding, tool authorization or completed business work. Use [acceptance](acceptance.md)
for destination-specific evidence.
