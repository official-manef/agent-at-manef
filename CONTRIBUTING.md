# Contributing

Thank you for improving agent portability. Start with a narrowly scoped issue or change: schema correctness, safe filesystem behavior, clear documentation, or a platform adapter backed by primary documentation.

## Local workflow

Use Python 3.10+. Clone the toolkit; no runtime dependencies are required. Create a feature branch. Add a synthetic regression before a bug fix. Run:

```sh
python -m unittest discover -s tests -v
python scripts/check_docs.py
python scripts/smoke.py
```

An optional editable installation uses `python -m pip install -e .`; this installs from the local source, not a promised PyPI release. Do not commit generated workspaces, private backups, build output or actual account data.

## Change requirements

Preserve preview-first behavior. Test source/target separation, conflict refusal, repeat application, rollback history and malicious archive paths. A parser test is not a runtime login test; a successful model response is not a security boundary. State which layers were actually tested.

New adapters must document exact files, current official sources, setup steps, unsupported behavior and a destination acceptance checklist. Never guess hosted APIs or import raw credential stores. Schema changes need a version/migration discussion; do not silently reinterpret old backups.

Documentation should include usable commands, prerequisites, expected results and limitations. Keep the English README and Indonesian guide aligned. Use relative links for this repository and official external sources for platform behavior.

## Review and conduct

Submit a pull request with rationale, changes, test evidence and remaining gaps. Keep criticism specific to code and behavior. Do not share private reports, user profiles or personal information. Respectful collaboration and explicit consent are required. See [SECURITY.md](SECURITY.md) for sensitive reports.

## Upstream and forks

The designated upstream is `rahmanef63/agent-at-manef`, pending transfer acceptance.
Until that destination resolves to repository ID `1414110928`, submit review branches
and PRs to the current [official-manef/agent-at-manef](https://github.com/official-manef/agent-at-manef).
Do not publish releases or treat the transfer as complete from this instruction alone. Keep each fork's tracking main
free of independent work; use feature branches and upstream PRs. Synchronization is explicit
and must never discard unique commits. See [governance](docs/governance.md).

Keep source credits accurate: repository ownership, maintenance responsibility and commit
attribution are distinct. Do not rewrite historical authorship during transfers.

Adapter changes require [conformance](docs/adapters.md); packaging requires the [release check](docs/release.md).
