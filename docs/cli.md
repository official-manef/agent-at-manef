# CLI reference

Run from the source checkout with `python -m agent_at_manef`. Optional local installation provides `agent-ssot`. All commands return JSON; success exits 0, a validation/conflict failure exits 1, and argparse usage errors exit 2. Error output intentionally avoids raw input/credential values.

## Workspace and agents

`init --target PATH [--apply]` prepares the fictional researcher starter. The destination must be new.

`new --workspace PATH --id SLUG --name NAME --owner OWNER --mission TEXT [--credential-name NAME ...] [--apply]` adds a new canonical agent. Existing identities are refused. Credential requirements are names only.

`doctor --workspace PATH` validates workspace/agent schema, canonical path rules, required charters/context and selected text patterns. No live accounts or external links are checked.

## Existing sources

`inventory --source PATH` discovers known instruction filenames without opening private config/session stores. Byte-identical groups are review candidates, not automatic identity merges. Narrow the source if the 512-candidate limit is reached.

`import --workspace PATH --source PATH --file RELATIVE_FILE --agent ID [--platform PLATFORM] [--apply]` stages one explicit Markdown/text file into the review inbox. It never promotes or modifies the original. Duplicate deterministic import destinations are refused rather than overwritten.

## Views and cleanup

`render --workspace PATH --target PATH --platform PLATFORM [--agent ID ...] [--apply]` previews/prepares the selected platform view. Without selection all canonical agents are included.

`reconcile` accepts the same options. Both names expose the same reconciliation engine; the latter emphasizes reviewing drift before updating an existing output.

`--quarantine-stale` only moves unchanged obsolete managed files when combined with `--apply`. Previous managed versions of updated files are archived automatically. Conflicts refuse the complete planned apply. No force or permanent-delete option exists.

Platforms: `generic`, `codex`, `claude`, `gemini`, `hermes`, `grokbot`. A different output platform should normally use a fresh target. The engine can show stale platform files explicitly, but it never disables an actual native agent or schedule.

`verify --target PATH` checks managed hashes. It does not inspect unrelated files, private env stores or native runtime state. It requires a valid local manifest and no active operation lock.

## Archives

`backup --workspace PATH --output FILE.zip [--apply]` creates a new, unencrypted context-only archive. The output must be outside the source and must not exist.

`restore --archive FILE.zip --target PATH [--apply]` validates before writing a new destination. Preview may use an internal temporary directory for schema verification, but does not modify the requested target. No native process starts.

`--version` prints the toolkit version. For exact parser help, use `python -m agent_at_manef COMMAND --help`.

## Offline capability discovery

```sh
python -m agent_at_manef capabilities
```

No arguments or workspace are needed. `kind`, `interface_version`, implementation version,
canonical/backup schema versions, available commands, adapter output levels and safety limits
are returned as JSON. This is a declaration, not a runtime health or authentication check.
Hosts must reject unsupported interface/schema versions rather than guess compatibility.
See [MSO consumer contract](integrations/mso.md).

## Branded aliases and assessment

Use either `python -m agent_at_manef` or the compatible `python -m agent_ssot`.
Source installation exposes both `agent-at-manef` and `agent-ssot` commands.
`assess --requirements <json> --target-profile <json>` is read-only and compares declarations;
exit 0 means declared compatibility, 2 means unmet requirements, and 1 means invalid input.
It never authorizes deployment. See [library contract](library.md).
