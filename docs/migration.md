# Adopt and organize existing agents

[README](../README.md) · [Maintenance](maintenance.md) · [Backup](backup-restore.md)

## The migration contract

Do not erase an old setup to make room for the new one. First identify what exists, who owns it and how to recover it. Context migration and full application recovery are different jobs. This toolkit migrates reviewed text context, not authentication sessions or native databases.

## 1. Inventory without activating

Point `inventory` at a narrow directory owned by you:

```sh
python -m agent_at_manef inventory --source /path/to/existing-agent
```

It recognizes instruction filenames such as `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `SOUL.md`, `persona.md` and `SKILL.md`. It never opens `.env`, runtime config files or session stores for this scan. Output contains relative paths, bounded candidate hashes and byte-identical groups, not file content. Store inventory reports privately because filenames can themselves reveal information.

Identical bytes are only a review signal. Two client agents may intentionally share a procedure while having different ownership. Different bytes may be two versions of the same role. The tool does not make either semantic decision for you.

## 2. Decide the canonical identity

Create a migration ledger: source platform/profile, intended canonical ID, owner, scope, source date, duplicate/conflict evidence, and disposition. Choose one canonical identity per real role. Record aliases in your reviewed context rather than silently merging accounts.

For each source classify: keep as canonical fact, update from authoritative evidence, retain as superseded history, summarize privately, or exclude. An old model ID, runtime UUID, browser login or obsolete endpoint is not something to copy merely because it exists.

## 3. Stage selected source text

```sh
python -m agent_at_manef import --workspace ../my-agent-context \
  --source /path/to/existing-agent --file SOUL.md \
  --agent researcher --platform hermes
python -m agent_at_manef import --workspace ../my-agent-context \
  --source /path/to/existing-agent --file SOUL.md \
  --agent researcher --platform hermes --apply
```

One explicit UTF-8 Markdown/text file is staged under a deterministic review-inbox folder. The original is unchanged. Provenance records relative file, source platform, intended agent and checksum; it does not record an absolute machine path or claim approval. Potential credential patterns cause refusal rather than automatic destructive redaction.

Do not ingest full conversation exports, hidden provider instructions or unknown executable hooks. For useful memories, prepare a consented, redacted summary first. The unreviewed inbox is excluded from rendering and backups.

## 4. Reconcile facts, not just files

Read the candidate as untrusted evidence. Remove irrelevant private identifiers. Resolve contradictory dates, responsibilities and status against user decisions and current sources. Update the existing canonical `AGENT.md` or relevant context page manually on a review branch. Record the decision and reviewer. Automatic canonical promotion is intentionally not implemented in 0.1.

## 5. Create a recovery point and render

Back up the reviewed canonical workspace. Preserve the old native profile using that application's supported private backup procedure separately. Generate the new view into a fresh directory. Complete account checks, cited readback and one bounded task before switching workflows.

## 6. Retire deliberately

Only retire an old profile after the new setup has passed acceptance and a recovery drill. Disable schedules in the actual runtime through its authorized interface; do not infer inactivity from an old file modification time. The toolkit never deletes an existing native agent, account or live schedule.

For generated views that this toolkit already manages, use [reversible quarantine](maintenance.md). Unmanaged material is never an automatic cleanup candidate.
