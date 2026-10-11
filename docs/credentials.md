# Credentials and account ownership

[Security](security.md) · [Platform guides](platforms.md)

An agent identity, a human account, an MCP client-to-server credential, a broker's downstream SaaS connection and a model-provider entitlement are separate things. A working connector listing does not prove the intended downstream account works.

## What belongs in this toolkit

The canonical agent descriptor may contain verified environment variable **names**. Rendering creates an empty `env.example`. No script reads that file as an environment, fills it, finds tokens on the machine or creates a master credential file.

```json
"credential_names": ["EXAMPLE_SERVICE_TOKEN"]
```

The example name above is illustrative, not a real provider contract. Inspect the selected runtime/provider's actual documentation before choosing names. OAuth-managed connections may need no environment variable at all. [MCP authorization](https://modelcontextprotocol.io/specification/latest/basic/authorization) describes protocol-level authorization; application/provider setup remains separate.

## Where values belong

Use the native provider-managed connection store, OS keychain or an approved secret manager. When a runtime requires a private `.env`, keep it outside the canonical workspace, public toolkit and generated view, under a per-identity configuration directory with appropriate ACLs. Never commit passwords, PATs, session cookies, OAuth refresh tokens, service-account JSON or authenticated webhook URLs.

Do not copy a parent's entire environment into every worker. Select the minimum account, project, tool and scope for the task. A separate filename or process environment does not stop a same-user process from reading another profile; strong isolation requires OS/container/account controls and server-side authorization.

## Verification record

For each required connection, record the canonical agent, account owner, authenticated subject reference, intended resource scope, private storage reference, permitted actions, expiry/rotation policy when known, and a harmless read-test result with date. Store references, never credential values.

Sharing a public agent blueprint does not authorize sharing its account. On another person's machine, they connect their own accounts. Credentials should not be distributed as part of a template or a portable-context backup.

## Cleanup and incidents

Unused credential references may be removed from a reviewed agent definition. That does not revoke the actual provider token; revocation is a distinct authorized action. Conversely, deleting a local credential file can break recovery without revoking any server-side access.

If a real secret leaks, rotate/revoke it through the provider, assess exposure and review history/copy cleanup. Do not advertise a pattern scan as a complete secret audit.
