"""Reviewed static adapters. Pure rendering; no external plugins, I/O or execution."""
from __future__ import annotations
from dataclasses import dataclass
import json
from types import MappingProxyType
from typing import Callable, Mapping

@dataclass(frozen=True)
class AgentView:
    id: str
    name: str
    mission: str
    charter: bytes
    guide: bytes

@dataclass(frozen=True)
class Adapter:
    id: str
    output_level: str
    filenames: tuple[str, ...]
    renderer: Callable[[AgentView], dict[str, bytes]]
    native_definition: bool = False

def _none(agent: AgentView) -> dict[str, bytes]:
    return {}

def _claude(agent: AgentView) -> dict[str, bytes]:
    return {"CLAUDE.md": agent.guide}

def _gemini(agent: AgentView) -> dict[str, bytes]:
    return {"GEMINI.md": agent.guide}

def _hermes(agent: AgentView) -> dict[str, bytes]:
    profile = json.dumps({"display_name": agent.name, "description": agent.mission}, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    return {"SOUL.md": agent.charter, "profile.yaml": profile.encode("utf-8")}

def _grokbot(agent: AgentView) -> dict[str, bytes]:
    profile = json.dumps({"name": agent.id, "title": agent.name, "description": agent.mission}, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    return {"profile-fields.json": profile.encode("utf-8"), "persona.md": agent.charter}

REGISTRY: Mapping[str, Adapter] = MappingProxyType({a.id: a for a in (
    Adapter("generic", "context-files", (), _none),
    Adapter("codex", "context-files", (), _none),
    Adapter("claude", "read-only-definition-files", ("CLAUDE.md",), _claude, True),
    Adapter("gemini", "context-files", ("GEMINI.md",), _gemini),
    Adapter("hermes", "profile-blueprint", ("SOUL.md", "profile.yaml"), _hermes),
    Adapter("grokbot", "app-settings-recipe", ("profile-fields.json", "persona.md"), _grokbot),
)})
PLATFORMS = tuple(REGISTRY)
MANAGED_FILENAMES = frozenset(n for a in REGISTRY.values() for n in a.filenames)

def describe() -> list[dict]:
    return [{"id": a.id, "output_level": a.output_level, "native_registration": False, "model_execution": False, "account_migration": False} for a in REGISTRY.values()]

def render(platform: str, agent: AgentView) -> dict[str, bytes]:
    try:
        adapter = REGISTRY[platform]
    except (KeyError, TypeError) as exc:
        raise ValueError("Unknown adapter") from exc
    files = adapter.renderer(agent)
    if set(files) != set(adapter.filenames) or any(type(b) is not bytes for b in files.values()):
        raise ValueError("Adapter output differs from declared contract")
    output = {"agents/" + agent.id + "/" + n: b for n, b in files.items()}
    if adapter.native_definition:
        output[".claude/agents/" + agent.id + ".md"] = ("---\nname: " + agent.id + "\ndescription: " + json.dumps("Read-only context for " + agent.name) + "\ntools: Read, Grep, Glob\n---\n\nRead agents/" + agent.id + "/AGENTS.md relative to the workspace. This definition grants no external actions.\n").encode()
    return output
