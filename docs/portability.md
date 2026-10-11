# Portability contract

[README](../README.md) · [Architecture](architecture.md) · [Capabilities](cli.md#offline-capability-discovery) · [Platform matrix](platforms.md)

## One canonical identity; several replaceable views

Agent SSOT treats identities, charters, curated knowledge, policies and decisions as owned
source data. Selecting a model, harness or machine must not silently rewrite that source.
Generated files are replaceable representations; native session stores and credentials are not.
This contract describes the implemented core and its explicit limits, not universal runtime parity.

| Boundary | Core guarantee | Outside the guarantee |
|---|---|---|
| Model/provider | No inference API dependency, model ID requirement or provider login in core operations | Identical behavior, token budgets, costs or reasoning across models |
| Harness/platform | Canonical schema is not a native harness profile; adapters emit views | Arbitrary plugin registration, automatic Bot creation or equal tool capability |
| Host/VM | No mandatory cloud vendor, hostname or baked-in user directory; paths supplied at invocation | Every CPU, operating system, browser, managed sandbox or serverless host running a chosen harness |
| MSO/host application | CLI can be consumed without copying core; MSO is optional | Already deployed MSO integration or implicit host authorization |
| Account | Credential names are portable references, not access grants | Migrating OAuth sessions, cookies, passwords or permission scopes |

## Required environment

The current CLI requires Python 3.10+ and a suitable local filesystem with permission to
create private files. It uses the standard library at runtime. Git is an acquisition and
collaboration tool, not a runtime requirement once source is present. Development/package
build tools are separate from runtime dependencies.

CI exercises Ubuntu, macOS and Windows according to the checked-in matrix. These checks
are evidence for that matrix, not proof of compatibility with untested CPU architectures,
mobile environments or filesystems. Owner-controlled containers, VMs and physical hosts can
use the same canonical format when these prerequisites are met. Cloud-specific infrastructure
setup and native runtime installation remain separate.

## Native formats are adapters, not alternative authorities

The built-in adapter list is currently finite: generic, Codex, Claude, Gemini, Hermes and
Grokbot. Unsupported platform identifiers are rejected rather than interpreted speculatively.
Use generic for another platform and explicitly verify its supported loading path. A future
adapter must preserve canonical bytes, scope, private-data boundaries and preview-first writes.

Changing a runtime's model or provider must happen in that runtime's private setup, not in the
canonical agent descriptor. Descriptors use a strict schema and reject unknown model/host fields.
Curated Markdown can discuss a project-specific dependency or dated technical observation;
that does not make it a global platform requirement. Review those references for freshness.

## Location-independent recovery

Backups contain relative canonical paths and verified file bytes, not the source machine's
absolute workspace path. A restored source in a different directory can render the same agent
on another supported platform. Tests compare source fingerprints and canonical payload across
six views and after relocation. They do not imply that live runtime state or filesystem ACLs
were migrated, or that archives are cryptographically authenticated.

If a user's Markdown itself contains old absolute paths, the toolkit does not rewrite that
prose or pretend those paths exist. Reconcile such references through source review. The tool's
path portability is not a semantic portability audit of every sentence.

## Discovery and compatibility

`python -m agent_ssot capabilities` returns an offline declaration with interface version,
implementation version, supported canonical/backup schemas, commands, output levels and limits.
It does not inspect the current machine or test a connection. Every readiness flag remains
false until a separate verifier provides actual evidence.

A consumer pins a tested release/source revision, accepts only schema/interface versions it
understands, tolerates documented additive fields and refuses unsupported behavior. The initial
0.1 command outputs are not an unversioned promise of indefinite API stability. Proposed format
changes need migration fixtures and a compatibility review before release.

## Acceptance evidence

Keep these distinct: prepared files, native discovery, source-cited context readback, authenticated
service read, bounded model task and continuity in another session. Passing one is not passing
all. No model requests are made in core portability tests. See [acceptance](acceptance.md).
