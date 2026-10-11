"""Synthetic guarded transport tests. Real-tool cases skip when tools are absent."""
from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile
from agent_at_manef import secure_transfer as secure
from agent_ssot import core

# Shape-only public recipient used for preview; real-tool cases generate temporary keys.
RECIPIENT = "age1" + "q" * 58


class SecureTransferTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.source = self.base / "source"
        core.init(self.source, True)
        self.archive = self.base / "context.zip"
        core.backup(self.source, self.archive, True)
        self.bundle = self.base / "delivery"
        self.key = self.base / "pinned-signer.pub"
        self.key.write_text("synthetic public fixture", encoding="utf-8")
        self.identity = self.base / "private-age.txt"
        self.identity.write_text("synthetic private fixture", encoding="utf-8")
        self.identity.chmod(0o600)

    def fake_bundle(self):
        self.bundle.mkdir()
        (self.bundle / secure.PAYLOAD).write_bytes(b"age-encryption.org/v1\nsynthetic")
        (self.bundle / secure.SIGNATURE).write_text("synthetic signature", encoding="utf-8")

    def test_encrypt_preview_does_not_execute_or_create_bundle(self):
        before = self.archive.read_bytes()
        with patch.object(secure, "_run", side_effect=AssertionError("No process")), patch.object(secure, "_binary", side_effect=AssertionError("No binary discovery")):
            result = secure.encrypt(self.archive, self.bundle, RECIPIENT)
        self.assertFalse(result["encrypted"])
        self.assertFalse(result["signature_verified"])
        self.assertFalse(self.bundle.exists())
        self.assertEqual(before, self.archive.read_bytes())

    def test_flags_must_be_real_booleans(self):
        with self.assertRaises(core.Refusal): secure.encrypt(self.archive, self.bundle, RECIPIENT, apply="yes")
        with self.assertRaises(core.Refusal): secure.verify(self.bundle, self.key, execute=1)
        with self.assertRaises(core.Refusal): secure.restore(self.bundle, self.base/"target", self.key, self.identity, apply="false")

    def test_only_native_recipient_shape_allowed(self):
        for value in ("ssh-ed25519 abc", "age1plugin1abc", "--help", RECIPIENT+";echo", None, ""):
            with self.subTest(value=type(value).__name__):
                with self.assertRaises(core.Refusal): secure.encrypt(self.archive, self.bundle, value)

    def test_encrypt_existing_bundle_not_touched(self):
        self.bundle.mkdir(); note=self.bundle/"work.txt";note.write_text("keep", encoding="utf-8")
        with self.assertRaises(core.Refusal): secure.encrypt(self.archive, self.bundle, RECIPIENT, apply=True)
        self.assertEqual(note.read_text(),"keep")

    def test_invalid_zip_refused_before_tools(self):
        self.archive.write_bytes(b"not a zip")
        with patch.object(secure,"_run",side_effect=AssertionError("No process")):
            with self.assertRaises(zipfile.BadZipFile): secure.encrypt(self.archive,self.bundle,RECIPIENT,apply=True)
        self.assertFalse(self.bundle.exists())

    def test_verify_and_restore_previews_do_not_execute(self):
        self.fake_bundle()
        with patch.object(secure,"_run",side_effect=AssertionError("No process")):
            v=secure.verify(self.bundle,self.key)
            r=secure.restore(self.bundle,self.base/"restored",self.key,self.identity)
        self.assertFalse(v["signature_verified"])
        self.assertFalse(r["decrypted"])
        self.assertFalse((self.base/"restored").exists())

    def test_missing_signature_refused(self):
        self.fake_bundle();(self.bundle/secure.SIGNATURE).unlink()
        with self.assertRaises(core.Refusal): secure.verify(self.bundle,self.key)

    def test_unexpected_bundle_file_refused(self):
        self.fake_bundle();(self.bundle/"instructions.md").write_text("untrusted",encoding="utf-8")
        with self.assertRaises(core.Refusal): secure.verify(self.bundle,self.key)

    def test_bundle_cannot_choose_its_own_trust_key(self):
        self.fake_bundle()
        with self.assertRaises(core.Refusal): secure.verify(self.bundle,self.bundle/secure.SIGNATURE)

    def test_expected_digest_checked_before_any_process(self):
        self.fake_bundle()
        with patch.object(secure,"_run",side_effect=AssertionError("No process")):
            for digest in ("0"*64,"oops"):
                with self.assertRaises(core.Refusal):secure.verify(self.bundle,self.key,expected_sha256=digest,execute=True)

    def test_snapshot_freezes_ciphertext_and_public_key(self):
        self.fake_bundle()
        with secure._snapshot(self.bundle,self.key) as (work,info):
            old=(work/secure.PAYLOAD).read_bytes()
            (self.bundle/secure.PAYLOAD).write_bytes(b"replacement")
            self.key.write_bytes(b"changed-public-key")
            self.assertEqual((work/secure.PAYLOAD).read_bytes(),old)
            self.assertEqual(info["ciphertext_sha256"],core.digest(old))
            self.assertNotEqual((work/"signer.pub").read_bytes(),self.key.read_bytes())

    def test_oversized_ciphertext_refused(self):
        self.fake_bundle()
        with (self.bundle/secure.PAYLOAD).open("wb") as f:f.truncate(secure.MAX_CIPHER+1)
        with self.assertRaises(core.Refusal):secure.verify(self.bundle,self.key)

    def test_existing_restore_target_preserved(self):
        self.fake_bundle();target=self.base/"restored";target.mkdir();(target/"work").write_text("keep")
        with self.assertRaises(core.Refusal):secure.restore(self.bundle,target,self.key,self.identity,apply=True)
        self.assertEqual((target/"work").read_text(),"keep")

    def test_source_target_overlap_refused(self):
        self.fake_bundle()
        with self.assertRaises(core.Refusal):secure.restore(self.bundle,self.bundle/"nested",self.key,self.identity)

    @unittest.skipIf(os.name=="nt","POSIX modes are not Windows ACLs")
    def test_shared_private_key_permissions_refused(self):
        self.fake_bundle();self.identity.chmod(0o644)
        with self.assertRaises(core.Refusal):secure.restore(self.bundle,self.base/"target",self.key,self.identity)

    def test_symlink_bundle_refused(self):
        self.fake_bundle();link=self.base/"linked"
        try:link.symlink_to(self.bundle,target_is_directory=True)
        except (OSError,NotImplementedError):self.skipTest("Symlinks unavailable")
        with self.assertRaises(core.Refusal):secure.verify(link,self.key)

    def test_external_execution_is_shell_free_with_minimal_environment(self):
        with patch.dict(os.environ,{"PROVIDER_API_KEY":"synthetic","AGE_PLUGIN_PATH":"untrusted","LD_PRELOAD":"untrusted"}), patch.object(subprocess,"run",return_value=SimpleNamespace(returncode=0)) as run:
            secure._run("/verified/tool",["-V","-m","file with spaces"],self.base)
        args,kw=run.call_args
        self.assertEqual(args[0],["/verified/tool","-V","-m","file with spaces"])
        self.assertNotIn("shell",kw)
        self.assertEqual(kw["env"]["PATH"],"")
        self.assertNotIn("PROVIDER_API_KEY",kw["env"])
        self.assertNotIn("LD_PRELOAD",kw["env"])
        self.assertNotIn("AGE_PLUGIN_PATH",kw["env"])
        self.assertIs(kw["stderr"],subprocess.DEVNULL)

    def test_failed_or_timed_out_external_tool_is_redacted(self):
        for failure in (SimpleNamespace(returncode=1),subprocess.TimeoutExpired("secret-canary",45)):
            kw={"side_effect":failure} if isinstance(failure,Exception) else {"return_value":failure}
            with patch.object(subprocess,"run",**kw):
                with self.assertRaises(core.Refusal) as caught:secure._run("/tool",[],self.base)
            self.assertNotIn("secret-canary",str(caught.exception))

    def test_missing_or_relative_binary_is_refused(self):
        with patch.object(shutil,"which",return_value=None):
            with self.assertRaises(core.Refusal):secure._binary("age")
        with self.assertRaises(core.Refusal):secure._binary("age","./untrusted")

    def test_cli_failure_does_not_echo_input(self):
        stream=io.StringIO()
        with redirect_stderr(stream):
            result=secure.main(["encrypt","--archive",str(self.archive),"--bundle",str(self.bundle),"--recipient","private-canary"])
        self.assertEqual(result,1)
        self.assertNotIn("private-canary",stream.getvalue())
        self.assertFalse(json.loads(stream.getvalue())["ok"])

    def test_cli_preview_json(self):
        stream=io.StringIO()
        with redirect_stdout(stream):
            code=secure.main(["encrypt","--archive",str(self.archive),"--bundle",str(self.bundle),"--recipient",RECIPIENT])
        self.assertEqual(code,0)
        self.assertFalse(json.loads(stream.getvalue())["external_tools_executed"])

    def test_encrypt_failure_keeps_source_and_no_delivery(self):
        before=self.archive.read_bytes()
        with patch.object(secure,"_binary",return_value="/age"),patch.object(secure,"_run",side_effect=core.Refusal("failed")):
            with self.assertRaises(core.Refusal):secure.encrypt(self.archive,self.bundle,RECIPIENT,apply=True)
        self.assertEqual(self.archive.read_bytes(),before)
        self.assertFalse(self.bundle.exists())


HAVE_TOOLS=all(shutil.which(name) for name in ("age","age-keygen","minisign"))


@unittest.skipUnless(HAVE_TOOLS,"Optional age/minisign tools not installed; real-tool CI runs separately")
class SecureRecoveryIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix="synthetic-security-fixtures-")
        cls.keys=Path(cls.temp.name).resolve()
        cls.addClassCleanup(cls.temp.cleanup)
        for label in ("right","wrong"):
            subprocess.run(["age-keygen","-o",str(cls.keys/(label+".identity"))],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            # -W is ONLY for throwaway test signing keys, never production setup guidance.
            subprocess.run(["minisign","-G","-W","-s",str(cls.keys/(label+".key")),"-p",str(cls.keys/(label+".pub"))],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        cls.recipient=subprocess.check_output(["age-keygen","-y",str(cls.keys/"right.identity")],text=True).strip()

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.base=Path(self.temp.name).resolve();self.source=self.base/"source";self.bundle=self.base/"bundle";self.target=self.base/"recovered"
        core.init(self.source,True);self.archive=self.base/"source.zip";core.backup(self.source,self.archive,True)
        secure.encrypt(self.archive,self.bundle,self.recipient,apply=True)
        self.sign()

    def sign(self):
        subprocess.run(["minisign","-S","-s",str(self.keys/"right.key"),"-m",str(self.bundle/secure.PAYLOAD),"-x",str(self.bundle/secure.SIGNATURE)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

    def restore(self,**kw):
        return secure.restore(self.bundle,self.target,self.keys/"right.pub",self.keys/"right.identity",apply=True,**kw)

    def test_real_roundtrip_and_verified_snapshot(self):
        digest=core.digest((self.bundle/secure.PAYLOAD).read_bytes())
        verified=secure.verify(self.bundle,self.keys/"right.pub",execute=True,expected_sha256=digest)
        self.assertTrue(verified["signature_verified"])
        report=self.restore(expected_sha256=digest)
        self.assertTrue(report["signature_verified"] and report["decrypted"] and report["restored"])
        self.assertFalse(report["signer_authorization_verified"])
        self.assertFalse(report["runtime_started"])
        self.assertEqual(core.load_workspace(self.source)[1],core.load_workspace(self.target)[1])
        self.assertEqual({p.name for p in self.bundle.iterdir()},{secure.PAYLOAD,secure.SIGNATURE})

    def test_real_ciphertext_tamper_blocks_before_decryption(self):
        path=self.bundle/secure.PAYLOAD;data=bytearray(path.read_bytes());data[-1]^=1;path.write_bytes(data)
        with patch.object(secure,"_run",wraps=secure._run) as run:
            with self.assertRaises(core.Refusal):self.restore()
        self.assertEqual(run.call_count,1)
        self.assertFalse(self.target.exists())

    def test_wrong_signing_key_blocks_before_decryption(self):
        with patch.object(secure,"_run",wraps=secure._run) as run:
            with self.assertRaises(core.Refusal):secure.restore(self.bundle,self.target,self.keys/"wrong.pub",self.keys/"right.identity",apply=True)
        self.assertEqual(run.call_count,1)
        self.assertFalse(self.target.exists())

    def test_wrong_age_identity_leaves_no_target(self):
        with self.assertRaises(core.Refusal):secure.restore(self.bundle,self.target,self.keys/"right.pub",self.keys/"wrong.identity",apply=True)
        self.assertFalse(self.target.exists())

    def test_valid_signature_cannot_bypass_inner_archive_path_validation(self):
        bad=self.base/"malicious.zip"
        with zipfile.ZipFile(bad,"w") as z:z.writestr("bundle.json","{}");z.writestr("../outside.md","untrusted")
        with (self.bundle/secure.PAYLOAD).open("wb") as out:
            subprocess.run(["age","-r",self.recipient,str(bad)],check=True,stdout=out,stderr=subprocess.DEVNULL)
        self.sign()
        with self.assertRaises(core.Refusal):self.restore()
        self.assertFalse(self.target.exists())
        self.assertFalse((self.base/"outside.md").exists())

    def test_invalid_inner_zip_cli_returns_redacted_failure(self):
        bad=self.base/"not-a-zip";bad.write_bytes(b"synthetic private canary")
        with (self.bundle/secure.PAYLOAD).open("wb") as out:
            subprocess.run(["age","-r",self.recipient,str(bad)],check=True,stdout=out,stderr=subprocess.DEVNULL)
        self.sign();stream=io.StringIO()
        with redirect_stderr(stream):
            code=secure.main(["restore","--bundle",str(self.bundle),"--trusted-key",str(self.keys/"right.pub"),"--identity",str(self.keys/"right.identity"),"--target",str(self.target),"--apply"])
        self.assertEqual(code,1)
        self.assertNotIn("synthetic private canary",stream.getvalue())
        self.assertFalse(self.target.exists())

    def test_valid_old_signature_does_not_override_pinned_digest(self):
        with patch.object(secure,"_run",side_effect=AssertionError("No process")):
            with self.assertRaises(core.Refusal):self.restore(expected_sha256="0"*64)
        self.assertFalse(self.target.exists())


if __name__=="__main__":unittest.main()
