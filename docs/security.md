# Threat model and operational limits

[Security reporting](../SECURITY.md) · [Architecture](architecture.md) · [Credentials](credentials.md)

## Intended environment

A trusted owner-controlled machine, reviewed source code, private canonical data and deliberate user actions. This is not an untrusted multi-tenant service. The canonical core has no network client or runtime-launch path. The separately invoked local action runtime executes explicitly selected, reviewed Python; agents that later read generated context may also have powerful tools.

## Threats and mitigations

| Threat | Implemented mitigation | Remaining responsibility |
|---|---|---|
| Accidental credential copy | Explicit canonical path/schema rules, file-type exclusions and selected pattern checks | Private content review; scanner is incomplete |
| Prompt injection in imported text | Candidates go to a non-active review inbox | Review source authority; runtime must not execute arbitrary instructions |
| Overwriting existing work | Preview-first writes, managed hashes, conflict refusal | Coordinate writers; do not edit output to change canonical identity |
| Destructive cleanup | Only unchanged obsolete managed output can be quarantined | Review native profiles separately; retain recovery copies |
| Path traversal/symlink escape | Relative-path validation, portable directory/file trees, symlink/reparse refusal and archive entry checks | Host access control; hostile concurrent same-user writes are out of scope |
| ZIP expansion/malformed bundle | Size/count limits, strict schema, digest and entry validation | Trusted acquisition, encryption/signature tooling |
| Cross-agent context exposure | Per-agent source selection plus explicitly shared folders | Scope shared files and enforce actual OS/account boundaries |
| False success claims | Separate context-file integrity from runtime/account/model acceptance | Run destination acceptance and record evidence |

## Non-goals

No cryptographic identity, signed backups, guaranteed secret/PII removal, malware scanning, authorization server, live-session migration, runtime sandbox, continuous sync or autonomous remediation. A checksum manifest is editable local data, not a trust root. A green CI badge certifies only the checks in that workflow.

Generated `SOUL.md`, `AGENTS.md` or app settings can influence a powerful agent. Inspect them before use. Do not automatically restore executable hooks, shell scripts or old schedules. Do not enable dangerous permission modes as a workaround for migration failures.

## Privacy in the public repository

Only generic code, documentation, examples and synthetic tests belong here. Do not copy a private workspace's Git history into this repository. Review commit authorship metadata, file paths and issue attachments as well as file contents. Reports can reveal private filenames even when they omit content.

## Concurrency and recovery

Cooperative operation locks do not protect against all races or hostile processes. Writes are atomic per file, not across a complete view. If an operation fails, inspect which files changed, preserve history and restore from a trusted canonical backup into a new directory. Never automatically unlock a currently running operation.

## Optional external security tools

The canonical core still has no runtime-launch or key-loading path. The separately invoked [secure transport module](secure-transfer.md) calls reviewed local age/minisign binaries with fixed arguments and explicit execution. The sender's public trust key and the recipient's private identity must be distinct files, including distinct filesystem identities; hardlinked aliases are refused before reading trust-key bytes. It is not automatic signing, organizational authorization, a replacement for encrypted disks, or a claim of safe execution of signed instructions.

## Optional local action runtime

The [runtime](runtime.md) uses exact routing, explicit execution, reviewed manifest/source
hashes, argument checks, policy-eligible planner metadata and a fresh child environment.
Generated code is staged as inactive data. There are no provider requests or automatic
candidate activation. A hash authenticates neither the author nor the declared effects.
The runner is process hygiene, not a sandbox: trusted Python can access same-user host
files, networking and process APIs. Use host-enforced isolation for untrusted code.
Declared write policy does not intercept filesystem/network system calls. Windows child
process-tree isolation and cross-platform memory limits are not supplied. Planner/model
credentials, deadlines and token budgets remain the embedding host's responsibility.
