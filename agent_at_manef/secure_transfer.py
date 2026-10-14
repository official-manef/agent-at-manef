"""Opt-in age/minisign transport; the canonical core remains offline and unchanged.

No cryptographic implementation, automatic key setup, shell or signing-key access.
Only explicit apply/execute starts the locally installed encryption/verification tools.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile
from agent_ssot import core

PAYLOAD = "context.zip.age"
SIGNATURE = PAYLOAD + ".minisig"
MAX_CIPHER = core.MAX_TOTAL + 2 * core.MAX_FILE
MAX_KEY = 16384
TIMEOUT = 45


class _RedactingArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        # argparse's default diagnostics echo raw paths, key-like tokens and values.
        self.exit(2, json.dumps({"ok": False, "error": "Invalid arguments; use --help for command options. Raw arguments are not returned."}) + "\n")


def _flag(value):
    if type(value) is not bool:
        raise core.Refusal("Execution requires an explicit boolean")


def _regular(path, limit):
    path = core.location(path)
    info = path.stat()
    if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= limit:
        raise core.Refusal("Expected a bounded nonempty regular file")
    return path


def _bytes(path, limit):
    path = _regular(path, limit)
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    core.no_links(path)
    if not 0 < len(data) <= limit:
        raise core.Refusal("File changed or exceeded limit")
    return data


def _outside(path, directory):
    if path == directory or directory in path.parents:
        raise core.Refusal("Trust and identity files must be outside the supplied bundle and output")


def _binary(name, override=None):
    if override is not None:
        path = Path(override).expanduser()
        if not path.is_absolute():
            raise core.Refusal("Explicit tool binary must be an absolute path")
        path = path.resolve()
    else:
        found = shutil.which(name)
        if found is None:
            raise core.Refusal("Required external tool is not installed")
        path = Path(found).resolve()
    if not path.is_file() or not os.access(path, os.X_OK):
        raise core.Refusal("External tool is not an executable file")
    return str(path)


def _run(binary, arguments, work, output=None):
    # Do not inherit provider keys, hooks, config paths or credential helper variables.
    # An empty PATH disables external age plugin discovery. This transport supports
    # native age identities only, with no interactive password or hardware plugin flow.
    env = {k: os.environ[k] for k in ("SystemRoot", "SYSTEMROOT", "SystemDrive", "WINDIR") if k in os.environ}
    env.update(PATH="", HOME=str(work), USERPROFILE=str(work), XDG_CONFIG_HOME=str(work),
               TMPDIR=str(work), TMP=str(work), TEMP=str(work), LANG="C", LC_ALL="C")
    options = {"start_new_session": True} if os.name != "nt" else {"creationflags": subprocess.CREATE_NO_WINDOW}
    try:
        process = subprocess.run([binary, *map(str, arguments)], cwd=work, env=env,
            stdin=subprocess.DEVNULL, stdout=output if output is not None else subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, timeout=TIMEOUT, check=False, **options)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise core.Refusal("External security tool failed or timed out; no raw output returned") from exc
    if process.returncode:
        raise core.Refusal("External security verification or encryption failed; no raw output returned")


@contextmanager
def _snapshot(bundle, trusted_key, expected_sha256=None):
    bundle = core.location(bundle)
    if not bundle.is_dir():
        raise core.Refusal("Expected an existing encrypted bundle directory")
    if {p.name for p in bundle.iterdir()} != {PAYLOAD, SIGNATURE}:
        raise core.Refusal("Bundle must contain exactly ciphertext and detached signature")
    key = _regular(trusted_key, MAX_KEY)
    _outside(key, bundle)
    payload = _bytes(bundle / PAYLOAD, MAX_CIPHER)
    signature = _bytes(bundle / SIGNATURE, MAX_KEY)
    public_key = _bytes(key, MAX_KEY)
    actual = core.digest(payload)
    if expected_sha256 is not None:
        if not isinstance(expected_sha256, str) or not re.fullmatch(r"[a-f0-9]{64}", expected_sha256) or expected_sha256 != actual:
            raise core.Refusal("Ciphertext does not match the pinned recovery digest")
    with tempfile.TemporaryDirectory(prefix="agent-secure-verify-") as td:
        work = Path(td).resolve()
        core.atomic(work / PAYLOAD, payload)
        core.atomic(work / SIGNATURE, signature)
        core.atomic(work / "signer.pub", public_key)
        # All verification and decryption use this same bounded private snapshot.
        yield work, {"ciphertext_sha256": actual, "signer_public_key_sha256": core.digest(public_key),
                     "expected_digest_matched": expected_sha256 is not None}


def _verify_snapshot(work, minisign_binary):
    _run(minisign_binary, ["-V", "-H", "-q", "-m", work / PAYLOAD,
         "-x", work / SIGNATURE, "-p", work / "signer.pub"], work)


def encrypt(archive, bundle, recipient, *, age_binary=None, apply=False):
    _flag(apply)
    if not isinstance(recipient, str) or not re.fullmatch(r"age1[023456789acdefghjklmnpqrstuvwxyz]{58}", recipient):
        raise core.Refusal("Select one verified native age X25519 recipient")
    archive = _regular(archive, core.MAX_TOTAL + core.MAX_FILE)
    bundle = core.separate(bundle)
    if bundle.exists() or bundle in archive.parents:
        raise core.Refusal("Use a new bundle directory separate from the original archive")
    # Read-only destination preview still validates the inner v1 schema in a temporary directory.
    with tempfile.TemporaryDirectory(prefix="agent-secure-source-") as td:
        work = Path(td).resolve()
        snapshot = work / "context.zip"
        core.atomic(snapshot, _bytes(archive, core.MAX_TOTAL + core.MAX_FILE))
        core.restore(snapshot, work / "validation-target", apply=False)
        report = {"ok": True, "mode": "apply" if apply else "preview", "encrypted": False,
                  "signature_verified": False, "signing_required": True, "external_tools_executed": False,
                  "original_archive_preserved": True, "plaintext_secure_erasure_guaranteed": False}
        if not apply:
            return report
        age = _binary("age", age_binary)
        cipher = work / PAYLOAD
        with cipher.open("xb") as out:
            _run(age, ["--encrypt", "--recipient", recipient, snapshot], work, out)
        encrypted = _bytes(cipher, MAX_CIPHER)
        if not encrypted.startswith(b"age-encryption.org/v1\n"):
            raise core.Refusal("External tool did not produce an age v1 payload")
        core.no_links(bundle)
        core.mkdir(bundle.parent)
        # Exclusive reservation prevents overwriting a concurrent/user destination.
        bundle.mkdir(mode=0o700)
        # Retain an incomplete reserved destination after I/O failure for inspection.
        core.atomic(bundle / PAYLOAD, encrypted)
        report.update(encrypted=True, external_tools_executed=True, ciphertext_sha256=core.digest(encrypted))
        return report


def verify(bundle, trusted_key, *, minisign_binary=None, expected_sha256=None, execute=False):
    _flag(execute)
    with _snapshot(bundle, trusted_key, expected_sha256) as (work, info):
        report = {"ok": True, "mode": "execute" if execute else "preview", **info,
                  "signature_verified": False, "external_tools_executed": False,
                  "signer_authorization_verified": False, "replay_policy_verified": False}
        if execute:
            _verify_snapshot(work, _binary("minisign", minisign_binary))
            report.update(signature_verified=True, external_tools_executed=True)
        return report


def restore(bundle, target, trusted_key, identity, *, age_binary=None, minisign_binary=None,
            expected_sha256=None, apply=False):
    _flag(apply)
    source = core.location(bundle)
    target = core.separate(target, source)
    if target.exists():
        raise core.Refusal("Restore requires a new target, never an existing workspace")
    key = _regular(trusted_key, MAX_KEY)
    identity = _regular(identity, MAX_KEY)
    for path in (key, identity):
        _outside(path, source)
        _outside(path, target)
    if key.samefile(identity):
        raise core.Refusal("Signing trust key and age private identity must be distinct")
    # Inspect mode/size only. Secret bytes are read only by the explicitly invoked age tool.
    if os.name != "nt" and stat.S_IMODE(identity.stat().st_mode) & 0o077:
        raise core.Refusal("Age identity permissions must not grant group or other access")
    with _snapshot(source, key, expected_sha256) as (work, info):
        report = {"ok": True, "mode": "apply" if apply else "preview", **info,
                  "signature_verified": False, "decrypted": False, "restored": False,
                  "external_tools_executed": False, "runtime_started": False,
                  "credential_values_returned": False, "signer_authorization_verified": False,
                  "replay_policy_verified": False, "windows_acl_verified": False,
                  "plaintext_secure_erasure_guaranteed": False}
        if not apply:
            return report
        minisign = _binary("minisign", minisign_binary)
        age = _binary("age", age_binary)
        _verify_snapshot(work, minisign)
        plain = work / "context.zip"
        with plain.open("xb") as out:
            _run(age, ["--decrypt", "--identity", identity, work / PAYLOAD], work, out)
        _regular(plain, core.MAX_TOTAL + core.MAX_FILE)
        # The verified signature never bypasses inner archive/schema/path validation.
        restored = core.restore(plain, target, apply=True)
        report.update(signature_verified=True, decrypted=True, restored=restored["ok"],
                      external_tools_executed=True, files=restored["files"])
        return report


def main(argv=None):
    parser = _RedactingArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    enc = sub.add_parser("encrypt", help="Preview/encrypt an existing v1 context ZIP; signing remains separate")
    enc.add_argument("--archive", required=True)
    enc.add_argument("--bundle", required=True)
    enc.add_argument("--recipient", required=True)
    enc.add_argument("--age-binary")
    enc.add_argument("--apply", action="store_true")
    for command in ("verify", "restore"):
        p = sub.add_parser(command)
        p.add_argument("--bundle", required=True)
        p.add_argument("--trusted-key", required=True, help="Out-of-band pinned signer public key, outside the received bundle")
        p.add_argument("--expected-sha256", help="Optional exact ciphertext digest from a trusted recovery record")
        p.add_argument("--minisign-binary")
        if command == "verify":
            p.add_argument("--execute", action="store_true")
        else:
            p.add_argument("--target", required=True)
            p.add_argument("--identity", required=True, help="Private age identity path outside source/target; never a key value")
            p.add_argument("--age-binary")
            p.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "encrypt":
            result = encrypt(args.archive, args.bundle, args.recipient, age_binary=args.age_binary, apply=args.apply)
        elif args.command == "verify":
            result = verify(args.bundle, args.trusted_key, minisign_binary=args.minisign_binary,
                            expected_sha256=args.expected_sha256, execute=args.execute)
        else:
            result = restore(args.bundle, args.target, args.trusted_key, args.identity,
                age_binary=args.age_binary, minisign_binary=args.minisign_binary,
                expected_sha256=args.expected_sha256, apply=args.apply)
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 0
    except (core.Refusal, OSError, ValueError, TypeError, KeyError, zipfile.BadZipFile, NotImplementedError):
        print(json.dumps({"ok": False, "error": "Secure transfer refused. Inspect trust, tools, permissions, archive and paths locally; no raw content returned."}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
