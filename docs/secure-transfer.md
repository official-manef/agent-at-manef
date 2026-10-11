# Encrypted transport and signature-verified recovery

[Backup contract](backup-restore.md) · [Security](security.md) · [Library](library.md)

This opt-in transport wraps an existing canonical v1 context ZIP with **age**, then requires
an independently trusted **minisign** signature before decrypting or restoring it. Cryptography
is performed by those established command-line tools, not a new implementation in this library.
The normal `backup`/`restore` commands still produce/consume unsigned, unencrypted v1 ZIP files.

## Scope and prerequisites

Use a trusted, private, owner-controlled filesystem with Python 3.10+, a reviewed age binary,
and a reviewed minisign binary. The toolkit never installs them. Core operations retain no
third-party runtime dependencies; only this optional module invokes external security tools.

The implemented noninteractive encryption contract accepts one native age X25519 recipient.
Native age identity files are used for decryption. Password prompts, SSH identities, hardware
plugins, recipient lists and post-quantum recipients are not supported by this wrapper. Use the
upstream tools directly under a reviewed procedure when those modes are required; do not force
an unsupported identity through this interface. The standard age file format is retained.

Authoritative command references reviewed 11 October 2026:
[age usage and installation](https://github.com/FiloSottile/age#usage) and
[minisign signing and verification](https://jedisct1.github.io/minisign/).
Local real-tool acceptance used age 1.2.1 and minisign 0.12. Linux CI checks the actual installed
versions. Cross-platform unit tests do not imply real-tool Windows/macOS acceptance.

## Keep three trust objects separate

The receiver supplies an **age public recipient** for encryption and privately retains its
age identity. The sender retains a **minisign signing key**. The receiver pins the sender's
**minisign public key** through a separate authenticated channel or trusted administrative store.
Never trust a public key just because it arrived alongside the bundle. The wrapper refuses a
trust key located inside the received bundle. Key names/folders are not proof of authorization.

Create and protect production keys through the upstream tools and your organization's approved
private procedure. `minisign -G` normally password-protects the signing key; sign interactively
outside this wrapper. Do not put keys or passphrases in Git, chat, command history, CI secrets
for tests, public artifacts, generated agent views or a parent environment shared by all agents.
The test suite's unencrypted signing keys are temporary fixtures, never production examples.

## Sender: validate, encrypt, then sign

First create a normal context-only backup in a private directory:

```sh
python -m agent_at_manef backup --workspace /private/context --output /private/context.zip --apply
```

Then preview encryption into a NEW directory. Replace the recipient placeholder with the
receiver's separately verified public age recipient; this placeholder is intentionally invalid.

```sh
python -m agent_at_manef.secure_transfer encrypt --archive /private/context.zip --bundle /private/delivery --recipient VERIFIED_AGE_RECIPIENT
python -m agent_at_manef.secure_transfer encrypt --archive /private/context.zip --bundle /private/delivery --recipient VERIFIED_AGE_RECIPIENT --apply
```

The original ZIP is validated and preserved, not deleted. Applied encryption produces
`delivery/context.zip.age`. The report says encrypted but **not signed**. Sign that ciphertext
with the sender's existing protected signing key in a private terminal:

```sh
minisign -S -s /private/keys/sender.key -m /private/delivery/context.zip.age -x /private/delivery/context.zip.age.minisig
```

Do not use minisign's password-disabling test flags for real signing keys. The resulting
transport directory contains exactly the ciphertext and its detached signature. Never add
private keys or arbitrary instruction files to it. Record the returned ciphertext SHA-256,
intended recipient/scope, source revision, backup date and retention decision in a separate
trusted recovery record. A signature by itself does not establish that this is the newest backup.

## Receiver: verify the sender before decrypting

```sh
python -m agent_at_manef.secure_transfer verify --bundle /private/incoming --trusted-key /private/trust/sender.pub
python -m agent_at_manef.secure_transfer verify --bundle /private/incoming --trusted-key /private/trust/sender.pub --execute
```

Without `--execute`, only input/size/path checks run; `signature_verified` stays false. Execution
uses minisign with hashed-signature enforcement, explicit public key and explicit signature
path. It does not emit the signed comments as instructions or log any payload/key contents.

Restore only into a NEW, dedicated destination:

```sh
python -m agent_at_manef.secure_transfer restore --bundle /private/incoming --trusted-key /private/trust/sender.pub --identity /private/keys/receiver.identity --target /private/restored-context
python -m agent_at_manef.secure_transfer restore --bundle /private/incoming --trusted-key /private/trust/sender.pub --identity /private/keys/receiver.identity --target /private/restored-context --apply
```

For exact-backup pinning, add `--expected-sha256` with the digest from the independent trusted
recovery record, not a digest selected from the incoming bundle. The wrapper reports whether
that pin matched. It does not implement organizational anti-rollback policy or key revocation.

An applied restore snapshots ciphertext, signature and the public key into a private temporary
directory. It verifies that snapshot, decrypts the SAME bytes, then runs all existing v1 archive,
path, size, checksum and schema validation before creating the destination. A valid signature
does not bypass inner archive validation. No fallback to unsigned recovery is attempted.

## What is actually enforced

Operations are preview-first. Existing bundle/restore destinations are refused. Inputs are
bounded regular files; symlink/reparse paths and overlapping destinations are refused. POSIX
private identity files must deny group/other access; Windows ACLs require separate review.

The wrapper does not read age private key contents itself or copy them into the transport;
the explicitly invoked age binary must read the designated identity. It never reads the sender's
signing key. External commands have fixed arguments, no shell, no interactive stdin, bounded
execution time, suppressed raw stdout/stderr and a minimal environment. Empty PATH disables age
plugin discovery. Explicit tool overrides must be absolute paths to reviewed executables.
This trusts the installed executables and host; it is not a sandbox against hostile same-user
processes, compromised binaries, inherited open handles, kernel access or filesystem races.

Plaintext temporarily exists while v1 validation/decryption runs. Temporary directories are
removed after normal completion/error, but deletion is NOT secure erasure, including on SSDs,
snapshots or crash recovery. Use encrypted local storage and approved recovery retention. An
interrupted publication can leave an incomplete reserved delivery directory; inspect it and use
a new destination. No cleanup command silently deletes that directory or old backups.

## Acceptance and failure modes

Real-tool tests cover round-trip context equivalence, ciphertext tampering, wrong signer key,
wrong age identity, signed invalid ZIP, signed path traversal, and a mismatched exact-backup pin.
Unit tests additionally cover preview/no subprocess, private-key permissions, no parent secret
environment, timeouts, source preservation, limits, missing signatures and redacted errors.

`signature_verified=true` means the pinned key verified the snapshot. It does not certify a
legal identity, account scope, license, current revocation status, model understanding or safe
execution of the contained agent instructions. Signer authorization and replay-policy fields
remain false. Apply the normal [destination acceptance](acceptance.md) afterward.

## Recovery and key rotation

Test restoration before retiring any old key. Keep an independently stored recovery identity
according to your retention policy; losing all age identities makes existing ciphertext
unrecoverable. Rotating a future encryption recipient does not re-encrypt historical bundles.
Rotating a signing key requires updating trusted public-key records through an authenticated
channel and retaining the appropriate historical trust/revocation policy. The toolkit never
performs provider token rotation or exports OAuth/session databases.

Unencrypted legacy v1 ZIPs remain readable by the original command; they are never upgraded to
trusted status merely because they passed a checksum. Repackaging them requires explicit local
encryption and signing. Source data, private account credentials, native runtime state and
transport trust are distinct recovery responsibilities.
