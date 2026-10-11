# Versioned catalog metadata

[Library](library.md) · [Example](../examples/catalog.json) · [Security](security.md)

```sh
python -m agent_at_manef catalog --file examples/catalog.json
```

`api.inspect_catalog(path)` provides the same read-only validation. The validator never fetches,
approves, installs or executes an entry. This is a local metadata contract, not a hosted registry.

Schema v1 contains immutable ID/version, agent/skill kind, publisher, license statement,
state, exact Git repository/revision/path/SHA-256, capability requirements, credential NAMES
and optional reviewer/date/evidence references. Versions use major.minor.patch with an optional
lowercase prerelease suffix. Catalog versions and Python package versions are distinct.

State progresses from draft to review to approved through authorized human review. Deprecated
and revoked records remain historical evidence. Approved declarations require review references,
but that label does not authenticate the reviewer. Return fields `review_verified`,
`source_verified` and `install_authorized` remain false. Do not silently change approved source
bytes at the same version; use a new version and review.

Before use, independently verify source bytes, revision, checksum, component license, publisher
and reviewer trust, required capabilities, account scope and destination. A checksum is not a
signature. Templates may not introduce executable hooks, implicit dependencies or credential
values. Markdown support does not imply executable skill package support.

The bundled example is explicitly synthetic and draft, with an invalid example domain and
zero-filled revision/digest. It demonstrates shape only and is not an installable recommendation.
Remote registries, verified signatures, downloads, runtime installation and automated revocation
are not implemented by this command. Existing context and backups stay unchanged.
