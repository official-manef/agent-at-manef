# Reconciliation, drift and reversible cleanup

[Migration](migration.md) · [Architecture](architecture.md) · [Troubleshooting](troubleshooting.md)

A generated view is disposable; its local edits are not disposable by assumption. `reconcile` compares desired output, current files and the previous managed manifest.

| Action | Meaning | Apply behavior |
|---|---|---|
| `create` | Desired file is absent | Create it |
| `unchanged` | Current bytes equal desired bytes | No write |
| `update` | Current bytes still equal the old managed version | Archive old bytes, write new bytes |
| `stale` | Previously managed file is no longer desired and unchanged | Retain, or quarantine only with explicit flag |
| `absent` | Obsolete managed file is already absent | Remove its stale manifest entry |
| `conflict` | Existing unmanaged or locally edited file differs | Refuse the entire planned apply before writes |

```sh
python -m agent_at_manef reconcile --workspace ../my-agent-context \
  --target ../my-view --platform codex
python -m agent_at_manef reconcile --workspace ../my-agent-context \
  --target ../my-view --platform codex --quarantine-stale --apply
```

Updates preserve previous managed files in `.ssot-history/<time>-<id>/`. With `--quarantine-stale`, unchanged obsolete files move there too. There is no automatic permanent deletion or history-retention timer. Local `.env` and unrelated notes are not read or removed by generated-output reconciliation.

## Before cleanup

Inspect the preview. Confirm the canonical source, selected platform/agents and owner. Back up reviewed canonical data. For unmanaged native installations, use the migration ledger and platform-specific backup process first; this command is not a general-purpose system cleaner.

## When there is a conflict

Do not suppress it with a force flag; none exists. Compare the local change privately against canonical context. Promote valid changes through review or preserve them elsewhere. After resolving the conflict, regenerate to a new view or restore the intended managed file and rerun preview.

## Recovery

Preserved old bytes can be inspected under `.ssot-history`. A prior output version is not automatically a fully coherent runtime snapshot. Prefer restoring a verified canonical backup into a new directory and rendering a fresh view. Validate before switching the runtime's working directory.

Interrupted multi-file updates can leave a partial view or an operation lock. Inspect process ownership and history before removing a stale lock. Do not delete a lock owned by an active process. Single-file replacement is atomic; the entire update is not transactional.

## Ongoing source hygiene

After material decisions and completed tasks, record a short source-backed summary. Date facts, keep acceptance separate from deployment and note what remains unknown. Do not add a permanent agent for every temporary task. A periodic review can be useful, but this toolkit schedules nothing on its own.
