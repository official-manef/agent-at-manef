"""Offline, additive interface discovery for host applications and adapters."""
from . import __version__, adapters, core

INTERFACE_VERSION = 1


def describe():
    """Return declared file-level capabilities, never detected runtime readiness.

    The command does not inspect user files, contact providers or launch programs.
    Hosts must separately pin the package revision and verify destination access.
    """
    return {
        "ok": True,
        "kind": "agent-ssot-capabilities",
        "interface_version": INTERFACE_VERSION,
        "product": {"name": "Agent@Manef", "slug": "agent-at-manef", "legacy_namespace": "agent_ssot"},
        "library_api_version": 1,
        "assessment_schema_versions": [1],
        "catalog_schema_versions": [1],
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
            "catalog": {"mutating": False, "declaration_comparison_only": True},
            "doctor": {"mutating": False},
            "inventory": {"mutating": False},
            "verify": {"mutating": False},
            **{name: {"mutating": True, "default_mode": "preview", "apply_flag": "--apply"}
               for name in ("init", "new", "import", "render", "reconcile", "backup", "restore")},
        },
        "adapters": adapters.describe(),
        "limits": {
            "max_file_bytes": core.MAX_FILE,
            "max_total_bytes": core.MAX_TOTAL,
            "max_files": core.MAX_FILES,
            "max_render_files": core.MAX_RENDER_FILES,
            "max_render_bytes": core.MAX_RENDER_TOTAL,
            "canonical_encoding": "utf-8",
            "backup_encrypted": False,
            "backup_signed": False,
            "os_sandbox": False,
        },
        "optional_transports": [{
            "id": "age-minisign", "module": "agent_at_manef.secure_transfer",
            "external_tools": ["age", "minisign"], "automatically_installed": False,
            "default_mode": "preview", "explicit_execution_required": True,
            "signing": "separate-private-operator-step", "signature_before_decryption": True,
            "private_key_read_by_external_age_only": True, "native_runtime_started": False,
            "real_tool_acceptance": "Linux CI; other OS integration not certified",
        }],
        "optional_runtime": {
            "module": "agent_at_manef.runtime", "schema_version": 1,
            "default_mode": "preview", "execution_flag": "--execute",
            "deterministic_command_routing": True, "planner": "host-supplied callback, unmatched only",
            "provider_requests_in_library": False, "automatic_candidate_activation": False,
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
