"""Versioned aliases; all implementation and state semantics remain in one core."""
from agent_ssot import api as implementation

API_VERSION = implementation.API_VERSION
capabilities = implementation.capabilities
assess = implementation.assess
inspect_workspace = implementation.inspect_workspace
render = implementation.render
backup = implementation.backup
restore = implementation.restore
verify = implementation.verify
__all__ = ["API_VERSION", "capabilities", "assess", "inspect_workspace", "render", "backup", "restore", "verify"]
