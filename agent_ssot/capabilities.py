"""Offline, additive interface discovery for host applications and adapters."""
from . import __version__, core

INTERFACE_VERSION = 1


def describe():
    """Return declared file-level capabilities, never detected runtime readiness.

    The command does not inspect user files, contact providers or launch programs.
    Hosts must separately pin the package revision and verify destination access.
    """
    levels = {
        "generic": "context-files",
        "codex": "context-files",
        "claude": "read-only-definition-files",
        "gemini": "context-files",
        "hermes": "profile-blueprint",
        "grokbot": "app-settings-recipe",
    }
    return {
        "ok": True,
        "kind": "agent-ssot-capabilities",
        "interface_version": INTERFACE_VERSION,
        "product": {"name": "Agent@Manef", "slug": "agent-at-manef", "legacy_namespace": "agent_ssot"},
        "library_api_version": 1,
        "assessment_schema_versions": [1],
        "implementation_version": __version__,
        "canonical_schema_versions": [core.VERSION],
        "backup_schema_versions": [core.VERSION],
        "declaration_only": True,
        "core": {
            "model_provider_required": False,
            "harness_required": False,
            "cloud_vendor_required": False,
            "mso_required": False,
            "network_requests": False,
            "runtime_processes_started": False,
            "credential_values_loaded": False,
            "runtime_dependencies": [],
            "python_minimum": "3.10",
            "filesystem_required": True,
        },
        "commands": {
            "capabilities": {"mutating": False},
            "assess": {"mutating": False, "declaration_comparison_only": True},
            "doctor": {"mutating": False},
            "inventory": {"mutating": False},
            "verify": {"mutating": False},
            **{name: {"mutating": True, "default_mode": "preview", "apply_flag": "--apply"}
               for name in ("init", "new", "import", "render", "reconcile", "backup", "restore")},
        },
        "adapters": [
            {"id": name, "output_level": levels[name], "native_registration": False,
             "model_execution": False, "account_migration": False}
            for name in core.PLATFORMS
        ],
        "limits": {
            "max_file_bytes": core.MAX_FILE,
            "max_total_bytes": core.MAX_TOTAL,
            "max_files": core.MAX_FILES,
            "canonical_encoding": "utf-8",
            "backup_encrypted": False,
            "backup_signed": False,
            "os_sandbox": False,
        },
        "readiness": {
            "destination_inspected": False,
            "provider_authenticated": False,
            "model_understanding_verified": False,
            "business_task_verified": False,
            "mso_integration_verified": False,
        },
    }
