"""Read-only catalog metadata; never fetch, approve, install or execute entries."""
from __future__ import annotations
from datetime import date
import re
from urllib.parse import urlsplit
from . import core

VERSION = 1
STATES = frozenset({"draft", "review", "approved", "deprecated", "revoked"})

def _text(value, limit=2000):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise core.Refusal("Invalid catalog text")
    core.checked(value.encode("utf-8"))

def _url(value):
    _text(value)
    try:
        parsed = urlsplit(value)
    except ValueError as exc:
        raise core.Refusal("Invalid catalog URL") from exc
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise core.Refusal("Source must be a plain HTTPS reference")

def validate(data: dict) -> dict:
    if not isinstance(data, dict) or set(data) != {"schema_version", "kind", "entries"}:
        raise core.Refusal("Unsupported catalog schema")
    if type(data["schema_version"]) is not int or data["schema_version"] != VERSION or data["kind"] != "agent-at-manef-catalog":
        raise core.Refusal("Unsupported catalog schema")
    if not isinstance(data["entries"], list) or len(data["entries"]) > 128:
        raise core.Refusal("Invalid entry count")
    core.checked(core.json_bytes(data))
    required = {"id", "kind", "version", "title", "publisher", "license", "state", "source", "requirements", "credential_names", "review"}
    seen = set(); rows = []
    for entry in data["entries"]:
        if not isinstance(entry, dict) or set(entry) != required:
            raise core.Refusal("Invalid catalog entry")
        ident = core.slug(entry["id"]); version = entry["version"]
        if not isinstance(version, str) or len(version) > 80 or not re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-[a-z0-9]+(?:[.-][a-z0-9]+)*)?", version):
            raise core.Refusal("Explicit semantic version required")
        if (ident, version) in seen:
            raise core.Refusal("Duplicate ID and version")
        seen.add((ident, version))
        if not isinstance(entry["kind"], str) or not isinstance(entry["state"], str) or entry["kind"] not in {"agent", "skill"} or entry["state"] not in STATES:
            raise core.Refusal("Unsupported kind or state")
        for field in ("title", "publisher", "license"):
            _text(entry[field], 240)
        source = entry["source"]
        if not isinstance(source, dict) or set(source) != {"repository", "revision", "path", "sha256"}:
            raise core.Refusal("Invalid source declaration")
        _url(source["repository"])
        for field, size in (("revision", 40), ("sha256", 64)):
            if not isinstance(source[field], str) or not re.fullmatch("[a-f0-9]{" + str(size) + "}", source[field]):
                raise core.Refusal("Immutable revision and digest required")
        core.relative(source["path"])
        for field, pattern in (("requirements", r"(?:model|harness|host|storage|protocol|tool)\.[a-z][a-z0-9_.-]*"), ("credential_names", r"[A-Z][A-Z0-9_]*")):
            names = entry[field]
            if not isinstance(names, list) or any(not isinstance(n, str) or not re.fullmatch(pattern, n) for n in names):
                raise core.Refusal("Invalid requirement names")
            if len(names) != len(set(names)):
                raise core.Refusal("Duplicate requirement")
        review = entry["review"]
        if review is not None:
            if not isinstance(review, dict) or set(review) != {"reviewer", "reviewed_on", "evidence"}:
                raise core.Refusal("Invalid review declaration")
            _text(review["reviewer"], 240); _url(review["evidence"])
            if not isinstance(review["reviewed_on"], str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", review["reviewed_on"]):
                raise core.Refusal("Review date required")
            try:
                date.fromisoformat(review["reviewed_on"])
            except ValueError as exc:
                raise core.Refusal("Invalid review date") from exc
        if entry["state"] == "approved" and review is None:
            raise core.Refusal("Approved declaration needs review references")
        rows.append({"id": ident, "version": version, "kind": entry["kind"], "title": entry["title"],
                     "publisher": entry["publisher"], "license": entry["license"], "state": entry["state"],
                     "review_declared": review is not None, "review_verified": False,
                     "source_verified": False, "install_authorized": False})
    return {"ok": True, "schema_version": VERSION, "entries": rows, "declaration_only": True,
            "remote_sources_fetched": False, "installed": False,
            "note": "Schema and references only. Verify source bytes, license, reviewer trust and scope separately."}

def inspect_file(path):
    return validate(core.obj(core.read(core.location(path))))
