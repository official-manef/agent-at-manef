# Architecture and authority

[README](../README.md) · [Agent schema](agent-spec.md) · [Threat model](security.md)

## Four layers, four responsibilities

| Layer | Owns | Must not become |
|---|---|---|
| Canonical workspace | Stable identities, charters, context, policies, decisions, procedures | A credential vault or raw transcript dump |
| Review inbox | Imported candidates with source platform, relative path and checksum | Automatically trusted instructions |
| Generated view | Runtime-specific context filenames and setup recipes | Another independently edited source of truth |
| Native runtime | Provider authentication, process execution, live sessions, tool permissions | Proof that canonical facts are correct |

The same agent can have several platform views. They share a stable identity and reviewed knowledge, not cookies, API tokens or a live process. Model behavior and token budgets remain platform-specific.

## Data flow

A user creates or reviews canonical material. `doctor` validates structure and selected safety constraints. `render` produces a view and a local managed-file manifest. Subsequent `reconcile` compares current bytes with the prior managed hashes and the newly desired output. This makes drift visible without replacing locally edited files.

A platform can produce a bounded handover or decision summary. The summary enters the review inbox. A human or authorized maintainer reconciles claims and updates canonical files under review. There is no background daemon or silent two-way sync.

The source fingerprint is a hash of canonical filenames and file hashes. It identifies the source bytes used for rendering; it is not a remote Git commit, digital signature, ACL or assertion that a model read them.

## Ownership and context budgeting

An agent has one explicit owner and a defined mission. Organizational hierarchy, runtime subagent hierarchy and credential ownership can be different relationships. Keep them explicit rather than deriving access from a folder name.

Each rendered agent includes only its own `agents/<id>/` subtree plus shared Markdown folders. Shared context should be genuinely shared. Move sensitive project material into the appropriate agent scope, or maintain separate tenant workspaces. This selection is not an OS sandbox.

The entrypoint links source files instead of concatenating every document into a giant prompt. The receiving runtime still needs to read complete relevant pages, cite them and state any unread or uncertain areas.

## File and transaction model

Canonical workspace JSON is deliberately small and strict. Text is UTF-8, bounded to 1 MiB per file, 512 files and 32 MiB per portable set. Paths must be relative, portable and non-symlinked.

New directories are prepared in a private sibling staging directory before installation. Managed file replacement is atomic per file. A multi-file update is not a database transaction. Cooperative locks prevent this tool's competing writers; they do not stop other software or hostile same-user processes. After an interruption, inspect the output and history, then re-run a preview. Do not delete somebody else's lock automatically.

`backup` exports canonical data only. `restore` checks paths, schema, count/size limits, entry types and checksums before creating a new destination. Encrypted/signature-verified backup transport and live native-state recovery belong to a separate process.

## Host integration without a second core

A host such as MSO consumes the versioned CLI contract and owns its user interface, permissions,
job orchestration and operational state. It does not become the agent knowledge authority.
Prefer a pinned package or source revision; do not copy this core into the host and evolve it
independently. An existing private knowledge format needs a reviewed mapping, not an assumed
schema match. See [portability](portability.md) and [integration contract](integrations/mso.md).
