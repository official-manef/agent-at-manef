"""Compare declared deployment requirements without probing or authorizing a runtime."""
from __future__ import annotations

from datetime import date
import json
import re
from . import core

SCHEMA_VERSION = 1
MAX_ITEMS = 128
MAX_DOCUMENT_BYTES = 65536
CAPABILITY = re.compile(r"(?:model|harness|host|storage|protocol|tool)\.[a-z][a-z0-9_.-]{0,95}")


def _document(value):
    if not isinstance(value, dict):
        raise core.Refusal("Expected an assessment object")
    try:
        encoded = json.dumps(value, allow_nan=False, ensure_ascii=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise core.Refusal("Assessment must be bounded JSON") from exc
    if len(encoded) > MAX_DOCUMENT_BYTES:
        raise core.Refusal("Assessment document is too large")
    core.checked(encoded)
    if type(value.get("schema_version")) is not int or value["schema_version"] != SCHEMA_VERSION:
        raise core.Refusal("Unsupported assessment schema")


def _names(value):
    if not isinstance(value, list) or len(value) > MAX_ITEMS:
        raise core.Refusal("Capability list is missing or too large")
    if any(not isinstance(name, str) or not CAPABILITY.fullmatch(name) for name in value):
        raise core.Refusal("Use a namespaced capability identifier")
    if len(value) != len(set(value)):
        raise core.Refusal("Duplicate capability requirement")
    return set(value)


def compare(requirements: dict, target: dict) -> dict:
    """Return declaration compatibility, not verified safety, login or permission.

    Missing and unknown required capabilities fail closed. A supported declaration must
    include a nonempty source/evidence reference and a valid observation date to count.
    References and dates are metadata; the caller must verify their truth and freshness.
    The function never reads environment variables, files, networks or provider state.
    """
    _document(requirements)
    _document(target)
    if set(requirements) != {"schema_version", "required", "optional"}:
        raise core.Refusal("Unknown requirement fields")
    required, optional = _names(requirements["required"]), _names(requirements["optional"])
    if required & optional:
        raise core.Refusal("A capability cannot be required and optional")
    if set(target) != {"schema_version", "target_id", "claims"}:
        raise core.Refusal("Unknown target fields")
    core.slug(target["target_id"])
    claims = target["claims"]
    if not isinstance(claims, dict) or len(claims) > MAX_ITEMS:
        raise core.Refusal("Invalid capability claims")
    _names(list(claims))
    for claim in claims.values():
        if not isinstance(claim, dict) or set(claim) != {"status", "evidence", "observed_at"}:
            raise core.Refusal("Invalid capability claim")
        if claim["status"] not in ("supported", "unsupported", "unknown"):
            raise core.Refusal("Unknown capability status")
        evidence = claim["evidence"]
        if not isinstance(evidence, str) or len(evidence) > 1024:
            raise core.Refusal("Evidence must be a bounded reference, never a credential")
        observed = claim["observed_at"]
        if observed is not None:
            if not isinstance(observed, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", observed):
                raise core.Refusal("Observation date must be ISO date or null")
            try:
                date.fromisoformat(observed)
            except ValueError as exc:
                raise core.Refusal("Invalid observation date") from exc
    rows = []
    for name in sorted(required | optional):
        claim = claims.get(name)
        if claim is None:
            status = "missing"
        elif claim["status"] == "supported" and (not claim["evidence"].strip() or claim["observed_at"] is None):
            status = "unsubstantiated"
        else:
            status = claim["status"]
        rows.append({"capability": name, "required": name in required, "status": status,
                     "satisfied_by_declaration": status == "supported"})
    blocked = [r["capability"] for r in rows if r["required"] and not r["satisfied_by_declaration"]]
    return {"ok": True, "kind": "agent-at-manef-assessment", "schema_version": SCHEMA_VERSION,
            "target_id": target["target_id"], "compatible_by_declaration": not blocked,
            "required_count": len(required), "blocked_requirements": blocked, "capabilities": rows,
            "evidence_verified": False, "evidence_freshness_checked": False,
            "runtime_probed": False, "deployment_authorized": False,
            "limits": "Self-declared evidence is not authorization, attestation or a successful live test"}
