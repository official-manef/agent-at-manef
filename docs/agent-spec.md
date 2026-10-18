# Canonical agent specification

[Getting started](getting-started.md) · [Example template](../templates/agent/agent.json)

The workspace root contains exactly this descriptor shape:

```json
{"kind": "agent-ssot-workspace", "schema_version": 1}
```

Each agent has `agents/<id>/agent.json`, `AGENT.md` and `context.md`.

```json
{
  "schema_version": 1,
  "id": "researcher",
  "name": "Researcher",
  "owner": "workspace-owner",
  "mission": "Research a bounded question and report cited findings.",
  "credential_names": []
}
```

Unknown fields are rejected in version 1. IDs are lowercase portable slugs, at most 48 characters, and must match their directory. Duplicate identities and common reserved device/path names are refused. Owner and mission cannot be empty. A credential list contains names only, without assigned values or inherited access.

## Charter

Describe responsibilities, non-goals, escalation/approval conditions and acceptance criteria. A useful charter says what the agent must deliver, where its authority ends, and how someone can tell whether it succeeded. Do not confuse the human owner with an AI role or use a model name as a permanent identity.

## Detailed context

The starter `context.md` is intentionally a prompt to curate knowledge, not a claim that the project is documented. Include purpose, users, scope/exclusions, stakeholder responsibilities, exact repo/branch rules, architecture, dated implementation/deployment status, private access references, runbooks, backlog, acceptance, risks and a next action. Link original sources and superseded decisions.

Add other Markdown files under that same agent directory as needed. Shared policy, decision and skill Markdown live in `policies/`, `decisions/`, and `skills/`. All shared folders are copied to each selected agent; do not put tenant-specific secrets or confidential material there.

Keep proposed, user-decided, source-observed and unknown facts distinct. A previous green test is not current production health. A canonical file is not evidence of a running agent or a successful login.

## Credentials and runtime configuration

Use `credential_names` only for verified variable requirements of the selected client. OAuth-managed services may require none. The generated `env.example` is blank and never loaded by the toolkit. Store values in the destination's private provider store or approved secret manager.

Model routing, tools, channels, schedules, session databases and native IDs are runtime configuration, not this canonical schema. The optional [local action runtime](runtime.md) has a separate versioned manifest. They require separate setup and acceptance. See [credentials](credentials.md).
