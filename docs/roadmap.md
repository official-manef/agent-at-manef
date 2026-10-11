# Roadmap and non-goals

[Changelog](../CHANGELOG.md) · [Contributing](../CONTRIBUTING.md)

## Available in 0.1

Canonical identity/context scaffolding, structural doctor, instruction-file inventory, explicit inbox import, six platform views, managed reconciliation with reversible quarantine, and context-only backup/validated restore. Standard-library core and synthetic cross-platform checks.

## Candidate improvements — not implemented promises

A reviewed semantic-diff interface for candidate promotion; explicit multi-tenant workspace export policies; signed/encrypted backup integration using established tools; versioned schema migrations; native capability probes and acceptance recipes for more runtimes; stronger adversarial filesystem/concurrency handling; structured context freshness audits.

Each needs a concrete scope, threat model, tests and honest platform evidence. A roadmap item is not a supported CLI option.

## Deliberate non-goals

Centralizing every user's credentials, exporting provider-hidden instructions, automatic public sharing, copying entire browser/session stores, assuming one account equals one agent, bypassing approvals, silent bidirectional sync, or claiming that a single prompt makes every model behave identically.

Quality is measured by fewer lost decisions, fewer conflicting agent identities, recoverable context and evidence-backed handovers—not by the number of bots or adapters listed.

## Host adoption

The offline capability declaration and MSO consumer design are available. Actual MSO UI/backend
wiring, private-workspace mapping, account setup and production acceptance remain separate work.
External adapter extension mechanisms may follow; arbitrary runtime IDs are not currently
accepted by the fixed built-in adapter list. Unknown platforms use generic explicitly.
