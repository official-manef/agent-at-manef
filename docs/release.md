# Release candidate and publication gates

[Library](library.md) · [Governance](governance.md) · [Contributing](../CONTRIBUTING.md)

Candidate **0.2.0rc1** retains API/workspace/output-state/backup version 1. Legacy namespace
`agent_ssot` and executable `agent-ssot` remain aliases of one implementation. A built candidate
is not a published registry release.

## Build and check

Run in a clean isolated contributor workspace, not a user's active runtime:

```sh
python -m pip install -r requirements-build.txt
python -m unittest discover -s tests -v
python scripts/check_docs.py
python scripts/smoke.py
python -m build --no-isolation --outdir dist
python scripts/release_check.py --dist dist > dist/release-report.json
```

Build tools are separate from runtime: the core has no third-party runtime dependencies. The
pins record tested direct build versions, not a hash-locked supply-chain proof; OS/Python-specific
transitive requirements may still be resolved. The checker inspects wheel/sdist contents,
rebuilds from the sdist, installs the wheel in a fresh venv without index/dependencies, then
exercises both module and console aliases and context recovery outside the source tree.

CI does this on Linux/Python 3.10, macOS/Python 3.12 and Windows/Python 3.12, retaining artifacts
and SHA-256 reports for 14 days. Artifacts are not a package registry, a signature or a permanent
release. Never include private context or runtime credentials.

## Publication gate

Complete the same-ID upstream transfer and verify creator/maintainer permissions and canonical
URLs. Review the exact PR, source revision, final CI and license metadata. Verify namespace
ownership through the provider's private interface. Prefer PyPI Trusted Publishing tied to a
reviewed upstream workflow and protected environment rather than storing a permanent token.
Do not publish from an unverified substitute upstream or rewrite existing release tags.

Only after authorized publication, install the registry artifact in a new environment and
verify its revision/provenance. No PyPI upload, npm package, release tag or publisher credential
is created by this utility. MSO and other consumers pin a tested version and check capabilities.

## Recovery

Install a verified older version into a separate environment, verify schema compatibility and
render behavior, then deliberately switch the consumer. Do not reset user checkouts or overwrite
private `.env` files. Unknown newer backup schemas must be rejected, not reinterpreted.

Primary sources: [PyPA packaging](https://packaging.python.org/en/latest/tutorials/packaging-projects/),
[metadata](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/),
[Trusted Publishing](https://docs.pypi.org/trusted-publishers/using-a-publisher/).

## 0.2.0rc2 continuation

This candidate adds opt-in age/minisign encrypted recovery, a separate Linux real-tool CI job, and failure-mode tests. Standard core tests may skip the optional real-tool class when binaries are absent; the dedicated secure recovery job requires them and fails rather than silently skipping. No registry release or key material is published.
