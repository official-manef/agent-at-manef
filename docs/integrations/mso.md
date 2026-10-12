# MSO and other host applications: consumer contract

[Architecture](../architecture.md) · [Portability](../portability.md) · [CLI](../cli.md) · [Acceptance](../acceptance.md)

**Status:** interface discovery and a proposed integration contract are supplied. This document
is not evidence of a live MSO deployment, account connection or migrated private workspace.
No MSO repository is changed by this toolkit's capability command.

## Responsibilities

| Component | Authority |
|---|---|
| Canonical private workspace | Reviewed agent identities, knowledge, policies and decisions |
| Agent@Manef | Validate, inventory, stage imports, render/reconcile and back up/restore canonical data |
| MSO or another host | User interface, task/workspace resolution, authentication, approvals, execution scheduling and live status |
| Agent harness | Model inference, tool invocation, session lifecycle and runtime-specific profiles |
| Host OS/container/VM | Files, processes, isolation, resources and private credential storage |

MSO consumes Agent@Manef; Agent@Manef must remain usable without MSO. Integrate a pinned package or
source revision instead of copying the core into a second implementation. The public toolkit
never becomes a store for a user's private operational records.

## Capability negotiation

The host first invokes the selected Python interpreter and pinned package with an argument
array, not a shell-constructed command:

```text
[python, "-m", "agent_ssot", "capabilities"]
```

Require `ok: true`, `kind: agent-ssot-capabilities`, `interface_version: 1`, and a compatible
canonical schema in `canonical_schema_versions`. Use the returned adapter IDs and output levels;
do not infer native runtime readiness from a matching platform name. Check the actual package
revision separately: the version string alone is not a signed supply-chain identity.

Capabilities are a declaration. `mso_integration_verified`, `provider_authenticated`, and other
readiness fields stay false because this CLI cannot observe those facts. A host's own verified
acceptance records must be separate from the toolkit declaration.

## Plan, approve, apply, verify

1. Resolve the signed-in user, tenant/project and intended agent before opening private paths.
2. Restrict source, generated output and backup paths to authorized private roots. Do not trust a
   caller-supplied path or model-generated command merely because schema validation passed.
3. Run `doctor`; discover the adapter; invoke a mutation without `--apply` for a preview.
4. Present changes/conflicts and check existing task authority. No silent conflict winner.
5. Execute the exact approved selection using `--apply`, a bounded timeout and a minimal environment.
6. Parse JSON and require a successful exit/result. Verify managed file integrity, then separately
   perform native/context/account/task acceptance when requested and authorized.
7. Keep output and paths private. Publish only deliberately redacted summaries; do not log secret
   values, full chat transcripts or unreviewed imported instructions.

The initial CLI's domain failures return a generic JSON error; argument parsing can emit usage
text with a nonzero exit. Treat malformed/non-JSON output, timeouts and unsupported interface
versions as explicit failures, not fabricated success. Pin and regression-test consumed command
outputs; the 0.1 package is not a frozen API for every future release.

## Import and source mapping

Existing knowledge layouts need a reviewed mapping to the generic schema. Stable source agent IDs
map to canonical `agents/<id>/agent.json`, `AGENT.md` and `context.md`; project scope, duties,
exclusions and dated facts remain in reviewed Markdown. Shared policies are genuinely shared.
Each agent has one canonical definition after migration.

Two-way automatic edits between an old format and the new format are not implemented. Choose the
existing private source as authority until mapping and acceptance pass. Stage selected source
text through the review inbox, resolve conflicting claims explicitly, and retain provenance.
Do not copy private templates or source histories into this public repository as fixtures.

## Evidence required before production adoption

Use synthetic fixtures for contract tests: new and existing agents, changed source, local output
conflicts, corrupt backup, relocation, invalid paths, unknown interface/schema, unavailable native
runtime, failed account access and mismatched tenant/project scope. Test recovery and permissions
in the host, not just the CLI.

Then perform one authorized real task and a fresh-session continuation on an owner-controlled
destination. Distinguish files prepared, context understood, native agent discovered, provider
connected, task completed and resumed. The public tests use no paid model or production credentials.
Native session/database recovery remains a separate private process.

## Library facade and requirements

Use `agent_at_manef.api` or the versioned JSON CLI from a pinned revision. `capabilities` exposes
library and assessment versions; `assess` compares separate model/harness/host requirements.
Neither trusts evidence automatically or grants scope. MSO must verify the current user/project,
private storage boundary, actual runtime capabilities and operation authority independently.
The legacy module/schema names remain supported. No production MSO dependency is wired by this
contract change, and a source fingerprint is not a deployment or account-identity attestation.
