# Troubleshooting

[CLI](cli.md) · [Security](security.md)

## The tool refuses an input without printing its contents

This is intentional: filenames, parser exceptions or candidate text can contain private values. Inspect locally. Check schema fields, UTF-8 encoding, size limits, unsafe paths, locally edited outputs and sensitive files. Do not paste your credential store into an issue to diagnose a refusal. Reproduce with synthetic data.

## A destination already exists

For init, new-agent creation, import or restore, select a fresh directory. For a managed generated view, use reconcile. There is no overwrite-everything option. Never reset another agent's checkout or clear a native profile to make installation pass.

## Reconcile reports conflict

A file is unmanaged or differs from its last managed version. Preserve it. Compare against canonical context privately, review any useful change, then regenerate into a new view or resolve the specific file. Do not edit the manifest to disguise a local edit.

## There is a lock after interruption

Confirm that the creating process has actually stopped. Preserve the lock while any writer may still be active. Inspect output/history and restore to a new directory if necessary. Locks coordinate this tool only, not other independently started programs.

## An archive passes checksums but comes from an unknown source

Do not treat it as trusted. The manifest is not signed, and an attacker can replace data and checksums together. Use trusted acquisition and approved encryption/signature tooling; read imported context as untrusted until reviewed.

## A file is excluded or too large

Runtime configs, credentials and databases are not portable context. Use the vendor's private recovery process for native state. Curate large transcripts into bounded reviewed summaries with provenance, rather than removing checks or claiming everything was read.

## The runtime does not see the new agent

Confirm the correct directory and native discovery rules. Some apps require reopening/reloading a workspace. Check the installed version's primary documentation. The toolkit creates files, not hosted bot registrations or processes.

## Authentication fails after migration

Authorize the destination account through its private provider setup. A template carries requirements, not the old login session. Never substitute a different client/admin account simply to make a test pass.

## Windows paths or permissions differ

Use `py -3` and single-line commands in PowerShell. Avoid reserved device names, colons inside relative filenames and reparse points. Review Windows ACLs independently; POSIX mode bits and Linux test success do not prove Windows access isolation.
