# Security policy

## Supported scope

The current 0.1.x source is an initial local-first toolkit. It has no hosted account service, telemetry collector or managed credential vault. Security fixes target the maintained default branch.

## Reporting a vulnerability

Do not open a public issue containing exploit-sensitive details, credentials, private agent context, account identifiers or session exports. Use GitHub's **Security → Report a vulnerability** when private reporting is enabled. Otherwise contact the repository owner privately through an already verified channel; do not place sensitive details in an issue merely because that button is absent. No response-time guarantee is offered.

For a normal bug, provide a minimal synthetic fixture, OS/Python version and bounded reproduction. The maintainer does not need a copy of your real `.env`, browser profile or conversation database.

## Important boundaries

The scanner uses selected patterns; it cannot detect every secret or personal detail. A green check is not permission to publish an archive. ZIP backups are not encrypted or signed. SHA-256 integrity is not authenticity. Imported text can contain prompt injection. Filesystem layouts and per-agent filenames do not isolate accounts or processes. See [the threat model](docs/security.md).

A leaked credential should be revoked/rotated through its provider before reviewing history cleanup. Deleting a file from the latest commit does not remove existing clones or logs. Do not rewrite history or revoke access as an automatic housekeeping task.
