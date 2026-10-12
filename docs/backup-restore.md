# Backup, restore and portability

[README](../README.md) · [Security](security.md) · [Acceptance](acceptance.md)

## Two backups, not one misleading promise

A portable context backup preserves what another platform can reasonably understand: identities, curated knowledge, decisions, policies and procedures. A native disaster-recovery backup may also need databases, attachments, application versions and encrypted secrets. These have different trust, format and recovery requirements.

**Agent@Manef implements the first kind only.** It does not clone an app, back up credentials, translate every message history, export provider-hidden memory or preserve every runtime customization.

## Included and excluded

| Included | Excluded |
|---|---|
| `workspace.json` | Git history and repository metadata |
| `agents/<id>/agent.json` | `.env`, cookies, keys, auth stores |
| Agent Markdown charter/context | Native session databases and raw logs/transcripts |
| Shared Markdown policies/decisions/skills | Generated output, local history and unreviewed inbox |

Every included file must pass the canonical schema/path/size rules and selected credential-pattern scanning. Unexpected files in canonical folders cause refusal instead of being silently forgotten. Put runtime/private files outside canonical directories; do not remove your only secret copy just to make a backup pass.

## Create a backup

```sh
python -m agent_at_manef doctor --workspace ../my-agent-context
python -m agent_at_manef backup --workspace ../my-agent-context --output ../context-2026-10-11.zip
python -m agent_at_manef backup --workspace ../my-agent-context --output ../context-2026-10-11.zip --apply
```

Output is a new ZIP with `bundle.json`, schema version, per-file SHA-256 and byte lengths. Existing archive names are refused. A backup file is private data even when its underlying toolkit is public.

**No encryption or signing is provided.** Store on controlled encrypted storage, and use your approved encryption/transport tooling when leaving the device. Obtain archives through trusted channels. An attacker who replaces both data and manifest can produce matching checksums.

## Restore and switch platform

```sh
python -m agent_at_manef restore --archive ../context-2026-10-11.zip --target ../recovered-context
python -m agent_at_manef restore --archive ../context-2026-10-11.zip --target ../recovered-context --apply
python -m agent_at_manef doctor --workspace ../recovered-context
python -m agent_at_manef render --workspace ../recovered-context --platform hermes --target ../hermes-view --apply
```

Restoration validates the manifest, complete canonical schema, checksums, unique case-insensitive filenames, relative paths, entry types and extraction limits before creating the requested destination. Symlinks, traversal, encrypted ZIP entries and unsupported schemas are refused. The destination must be new, never your active home/profile.

Limits: 1 MiB per text file, 512 canonical files and 32 MiB total canonical data. Larger workspaces need deliberate segmentation or a reviewed future format; there is no unsafe override.

## Recovery drill

Choose a backup, restore on a clean directory or machine, validate the context, render another platform, reconnect required accounts privately and perform the acceptance checklist. Record exact source/version, restored IDs, unresolved gaps and one successful bounded task. Start another session to test continuity in that runtime.

A successful ZIP extraction is not a complete recovery drill. A successful database read is not evidence the model understood the right context. Keep old native backups until the migration owner accepts the new environment.

## Optional secure transport

The standard ZIP and its schema remain unchanged. Use the [opt-in age/minisign workflow](secure-transfer.md) for encrypted delivery and signature-verified recovery. It uses existing external tools only after explicit execution; plaintext ZIP checksums alone still do not authenticate a sender.
