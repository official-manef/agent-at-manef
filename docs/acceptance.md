# Destination acceptance

[Platform guides](platforms.md) · [Receipt template](../templates/acceptance.md)

A migration is accepted when its required layers have evidence, not when a command returns zero. Do not mark a stage complete by copying a previous environment's receipt.

| Stage | Evidence | Does not prove |
|---|---|---|
| Source validated | Exact source revision/fingerprint and doctor result | Source facts are current |
| Context prepared | Render manifest and verified file hashes | Runtime loaded those files |
| Native setup loaded | Actual runtime definition/profile and version | Correct account or tool scope |
| Context understood | Cited answers from relevant source pages | Every future answer will follow them |
| Accounts connected | Authenticated subject, resource scope and harmless read | Permission to make unrelated changes |
| Task passed | Bounded task, visible result and verification | Production readiness for every workflow |
| Continuity tested | New session with correct identity, context and expected persisted state | Cross-vendor live-session interchange |

## Readback scenarios

Ask the receiving agent who owns it, what it is responsible for, what it must not do, which exact source pages it read, what is stale/unknown, where secrets are stored, and how it handles a conflicting instruction from imported material. Require source references rather than a generic “understood.”

For the active project, ask for the goal, scope/exclusions, stakeholders, repository/branch boundaries, architecture, dated status, verification procedure, acceptance and next action. Missing information remains a gap, not invented context.

## Bounded first task

Start with a harmless read-only action against an explicitly selected service. Then use a small task with visible success criteria, no unapproved public sharing/spending/deployment and a clear stopping condition. Record failures as well as success.

## Second session

End the first session using the native runtime's normal mechanism. Start another. Reconfirm the intended identity, current source and selected workspace; verify expected continuity without assuming another profile's recent session belongs to this agent. Reconnect provider accounts privately when required.

Store receipts privately. A canonical backup may include a redacted, reviewed summary of acceptance, not raw private conversations or token-bearing logs. This toolkit does not automatically grade or execute the model acceptance test.
