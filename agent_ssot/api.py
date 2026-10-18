"""Small versioned facade for local hosts. Mutations remain explicit and preview-first."""
from __future__ import annotations

from pathlib import Path
from . import catalog, assessment, capabilities as capability_contract, core

API_VERSION = 1


def capabilities() -> dict:
    return capability_contract.describe()


def assess(requirements: dict, target: dict) -> dict:
    return assessment.compare(requirements, target)


def inspect_workspace(workspace: str | Path) -> dict:
    _, files, agents = core.load_workspace(workspace)
    return {"ok": True, "agents": sorted(agents), "files": len(files),
            "source_fingerprint": core.digest(core.json_bytes({n: core.digest(d) for n, d in sorted(files.items())})),
            "credential_values_returned": False, "runtime_verified": False}


def render(workspace: str | Path | core.WorkspaceSnapshot, target: str | Path, platform: str, *,
           agents: list[str] | None = None, apply: bool = False, quarantine_stale: bool = False) -> dict:
    if type(apply) is not bool or type(quarantine_stale) is not bool:
        raise core.Refusal("Apply and quarantine must be explicit booleans")
    return core.reconcile(workspace, target, platform, agents, apply, quarantine_stale)


def backup(workspace: str | Path, output: str | Path, *, apply: bool = False) -> dict:
    if type(apply) is not bool:
        raise core.Refusal("Apply must be an explicit boolean")
    return core.backup(workspace, output, apply)


def restore(archive: str | Path, target: str | Path, *, apply: bool = False) -> dict:
    if type(apply) is not bool:
        raise core.Refusal("Apply must be an explicit boolean")
    return core.restore(archive, target, apply)


def verify(target: str | Path) -> dict:
    return core.verify(target)


def inspect_catalog(path: str | Path) -> dict:
    return catalog.inspect_file(path)


def prepare_workspace(workspace: str | Path) -> core.WorkspaceSnapshot:
    """Validate once for repeated renders; explicit refresh observes later changes."""
    return core.snapshot(workspace)
