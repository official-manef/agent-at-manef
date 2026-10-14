# Local lifecycle user stories and QA

[CLI](cli.md) · [Library](library.md) · [Destination acceptance](acceptance.md)

These stories cover the offline toolkit and optional local encryption tools. Every
fixture is synthetic. A completed file workflow does not establish runtime loading,
account access, model understanding or production readiness.

## Roles and expected flows

| Role and user story | Flow | Acceptance |
|---|---|---|
| Workspace owner: define an accountable agent without losing existing context | `init` preview → apply → `doctor` → `new` preview → apply → `doctor` | Preview creates no requested destination; duplicate identities and aggregate workspace-limit violations refuse before writes. |
| Migration owner: preserve an existing setup while reviewing selected knowledge | `inventory` → explicit `import` preview → apply → review inbox | Credential/config/session stores remain unread; original files stay unchanged; imported text is inactive and excluded from render/backup. An unreadable directory refuses the scan. |
| Agent maintainer: prepare a scoped platform view | `doctor` → selected-agent `render` preview → apply → `verify` | All six adapters preserve canonical bytes; selected agents do not include peer context; an explicit empty library selection refuses. Rendering starts no runtime. |
| Agent maintainer: reconcile a reviewed source update safely | Edit canonical context → `reconcile` preview → apply → `verify` | Unchanged managed output updates with previous bytes in history; local edits and unmanaged collisions refuse the complete apply; unrelated files remain untouched. |
| Migration owner: switch platforms with recoverable obsolete output | `reconcile` preview → optional `--quarantine-stale --apply` → `verify` | Only unchanged obsolete managed files move into history. Edited obsolete output refuses; no permanent cleanup occurs. |
| Recovery owner: move canonical context to a new directory | `backup` preview → apply → `restore` preview → apply → `doctor` → render another platform | New archive/destination required; descriptors, reviewed context and fingerprints survive relocation; inbox, credentials and live sessions stay excluded. |
| Security-conscious recovery owner: verify encrypted delivery before recovery | Encrypt preview → apply → sign privately → verify preview → execute → restore preview → apply | Pinned public trust is outside the bundle; private identity has private POSIX permissions; trust/identity hardlink aliases refuse before key reads; signature and optional pinned digest checks precede decryption; the inner ZIP still passes canonical validation. |
| Host integrator: inspect compatibility without accidentally granting authority | `capabilities` → `assess` → optional local `catalog` inspection | Metadata is read-only and contains no secret values. Missing required claims fail closed; declared compatibility never authorizes execution or deployment. |

## Failure and boundary scenarios

| Scenario | Required behavior | Synthetic evidence |
|---|---|---|
| Traversal, symlink/reparse path, global profile or overlapping source/target | Refuse before destination writes | [Core tests](../tests/test_core.py) |
| Case aliases in directories, file/directory conflicts, Windows device names or invalid filename characters | Refuse on every host before archive staging/output writes | [Core tests](../tests/test_core.py) |
| Canonical folder is a file, dangling link or unreadable directory | Refuse rather than silently omit context | [Core tests](../tests/test_core.py) |
| Malformed schema, boolean/floating-point version, noninteger byte size, duplicate JSON keys or excessive nesting | Refuse with bounded, redacted diagnostics | [Core tests](../tests/test_core.py) and [library tests](../tests/test_library.py) |
| Unsupported or damaged ZIP compression, unsafe entries, checksum mismatch or oversized archive | Refuse and leave requested restore destination absent | [Core tests](../tests/test_core.py) and [secure transport tests](../tests/test_secure_transfer.py) |
| Unknown command or option containing a private canary | JSON stderr, exit 2, no raw argument echo | [CLI encoding tests](../tests/test_cli_encoding.py) and [secure transport tests](../tests/test_secure_transfer.py) |
| Wrong signer, ciphertext tamper, wrong age identity or replay against a pinned digest | Stop recovery without creating the destination | [Optional actual-tool tests](../tests/test_secure_transfer.py) |
| Operation lock or a locally edited generated file | Retain the lock/edit and refuse apply | [Core tests](../tests/test_core.py) and [adapter tests](../tests/test_adapters.py) |

## Running the checks

```sh
python -m unittest discover -s tests -v
python scripts/check_docs.py
python scripts/smoke.py
```

The smoke check invokes the real local CLI across six adapters and a backup/restore
round trip. It uses no provider credentials and launches no agent runtime.

Install trusted `age`, `age-keygen` and `minisign` binaries on the local PATH to run
the optional encryption/recovery tests instead of skips. Use the
[release checks](release.md) for wheel/source-archive and offline-install validation.

Native instruction discovery, private account authorization, model readback, useful
task acceptance and second-session continuity still require the separate
[destination acceptance checklist](acceptance.md). They are not graded by this suite.
