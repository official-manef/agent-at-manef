"""Command line interface; every mutating operation defaults to preview."""
import argparse
import json
import sys
import zipfile
from . import catalog, __version__, assessment, capabilities, core


class RedactingParser(argparse.ArgumentParser):
    def error(self, message):
        # argparse normally echoes unknown options and invalid argument values.
        self.exit(2, json.dumps({"ok": False,
            "error": "Invalid arguments; use --help for command options. Raw arguments are not returned."}) + "\n")


def main(argv=None):
    parser = RedactingParser(description="Agent@Manef — define, reconcile and move curated agent context.")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("capabilities", help="Report offline interface/schema/adapter contracts, not runtime readiness")
    c = sub.add_parser("catalog", help="Validate local metadata; never install entries")
    c.add_argument("--file", required=True)
    p = sub.add_parser("assess", help="Compare declared model/harness/host requirements; never authorize deployment")
    p.add_argument("--requirements", required=True)
    p.add_argument("--target-profile", required=True)
    p = sub.add_parser("init", help="Preview/create a private canonical workspace")
    p.add_argument("--target", required=True)
    p.add_argument("--apply", action="store_true")
    p = sub.add_parser("new", help="Preview/add a canonical agent")
    p.add_argument("--workspace", required=True)
    for field in ("id", "name", "owner", "mission"):
        p.add_argument("--" + field, required=True)
    p.add_argument("--credential-name", action="append", default=[])
    p.add_argument("--apply", action="store_true")
    p = sub.add_parser("doctor", help="Validate canonical schema and curated content")
    p.add_argument("--workspace", required=True)
    p = sub.add_parser("inventory", help="Read-only candidate/identical-content inventory of an existing setup")
    p.add_argument("--source", required=True)
    p = sub.add_parser("import", help="Stage one explicitly selected context file for human review")
    p.add_argument("--workspace", required=True)
    p.add_argument("--source", required=True)
    p.add_argument("--file", required=True)
    p.add_argument("--agent", required=True)
    p.add_argument("--platform", choices=core.PLATFORMS, default="generic")
    p.add_argument("--apply", action="store_true")
    for name in ("render", "reconcile"):
        p = sub.add_parser(name, help="Preview/render a platform view; reconcile detects drift and local edits")
        p.add_argument("--workspace", required=True)
        p.add_argument("--target", required=True)
        p.add_argument("--platform", choices=core.PLATFORMS, required=True)
        p.add_argument("--agent", action="append")
        p.add_argument("--quarantine-stale", action="store_true", help="Move only unchanged obsolete managed files into local history")
        p.add_argument("--apply", action="store_true")
    p = sub.add_parser("verify", help="Verify managed output hashes, not model understanding")
    p.add_argument("--target", required=True)
    p = sub.add_parser("backup", help="Preview/create a context-only ZIP; not encrypted")
    p.add_argument("--workspace", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--apply", action="store_true")
    p = sub.add_parser("restore", help="Verify and restore a bundle only into a new directory")
    p.add_argument("--archive", required=True)
    p.add_argument("--target", required=True)
    p.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    try:
        cmd = args.command
        if cmd == "catalog":
            result = catalog.inspect_file(args.file)
        elif cmd == "capabilities":
            result = capabilities.describe()
        elif cmd == "assess":
            result = assessment.compare(core.obj(core.read(args.requirements)), core.obj(core.read(args.target_profile)))
        elif cmd == "init":
            result = core.init(args.target, args.apply)
        elif cmd == "new":
            result = core.new_agent(args.workspace, args.id, args.name, args.owner, args.mission, args.credential_name, args.apply)
        elif cmd == "doctor":
            _, files, agents = core.load_workspace(args.workspace)
            result = {"ok": True, "files": len(files), "agents": sorted(agents), "live_connections_checked": False,
                      "limits": "Structural validation and pattern scanning do not prove semantic accuracy or absence of all secrets/PII."}
        elif cmd == "inventory":
            result = core.inventory(args.source)
        elif cmd == "import":
            result = core.import_context(args.workspace, args.source, args.file, args.agent, args.platform, args.apply)
        elif cmd in {"render", "reconcile"}:
            result = core.reconcile(args.workspace, args.target, args.platform, args.agent, args.apply, args.quarantine_stale)
        elif cmd == "verify":
            result = core.verify(args.target)
        elif cmd == "backup":
            result = core.backup(args.workspace, args.output, args.apply)
        else:
            result = core.restore(args.archive, args.target, args.apply)
        print(json.dumps(result, ensure_ascii=True, indent=2))
        if cmd == "assess" and not result["compatible_by_declaration"]:
            return 2
        return 0 if result["ok"] else 1
    except (core.Refusal, OSError, ValueError, TypeError, KeyError, zipfile.BadZipFile):
        # Do not echo hostile filenames, imported content or credential-bearing exception strings.
        print(json.dumps({"ok": False, "error": "Refused: inspect schema, paths, local edits and private data locally. No raw content is returned."}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
